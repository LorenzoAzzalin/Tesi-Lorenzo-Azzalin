import zipfile
import os
import xarray as xr
import gc
import time

# Definizione dei percorsi coerenti con la struttura del progetto.
# I dati grezzi vengono letti dalla cartella "dati_grezzi"
# e trasformati nella cartella "preprocessing".
cartella_root = "dataset_intero"
cartella_preparazione = os.path.join(cartella_root, "preparazione_dati")

cartella_grezzi = os.path.join(cartella_preparazione, "dati_grezzi")
cartella_output = os.path.join(cartella_preparazione, "preprocessing")

os.makedirs(cartella_output, exist_ok=True)


# Funzione per forzare la rappresentazione della variabile temporale come stringa.
# Questo passaggio è utile per l'esportazione in CSV, evitando la perdita della componente oraria
# che può verificarsi con alcune rappresentazioni di datetime.
def forza_datetime_per_csv(dataset, variabile_tempo="valid_time"):
    if variabile_tempo in dataset.coords:
        dataset = dataset.copy()
        dataset[variabile_tempo] = dataset[variabile_tempo].dt.strftime("%Y-%m-%d %H:%M:%S")
    return dataset


# Individuazione automatica delle regioni a partire dai dati grezzi.
# Questo rende lo script indipendente dal numero di regioni presenti.
regioni = [
    nome for nome in os.listdir(cartella_grezzi)
    if os.path.isdir(os.path.join(cartella_grezzi, nome))
]

print("Regioni trovate:", regioni)


# Loop principale sulle regioni
for regione in regioni:

    print("\nRegione:", regione)

    # cartella con i dati grezzi della regione
    cartella_regione_grezzi = os.path.join(cartella_grezzi, regione)

    # cartella di output per il preprocessing della regione
    cartella_regione_preprocessing = os.path.join(cartella_output, regione)

    os.makedirs(cartella_regione_preprocessing, exist_ok=True)

    # Separazione tra dati meteorologici e dati ondosi.
    # Questa distinzione è necessaria perché:
    # - provengono da componenti diverse del modello ERA5
    # - verranno successivamente trattati con pipeline differenti (regridding)
    cartella_meteo = os.path.join(cartella_regione_preprocessing, "meteo")
    cartella_onde = os.path.join(cartella_regione_preprocessing, "onde")

    os.makedirs(cartella_meteo, exist_ok=True)
    os.makedirs(cartella_onde, exist_ok=True)

    # Selezione dei file NetCDF o ZIP presenti nella cartella
    file_input = [
        f for f in os.listdir(cartella_regione_grezzi)
        if f.endswith(".nc") or f.endswith(".zip")
    ]

    if len(file_input) == 0:
        print("Nessun file trovato")
        continue

    for nome_file in file_input:

        print("\nFile:", nome_file)

        percorso_file = os.path.join(cartella_regione_grezzi, nome_file)

        # Cartella temporanea per l'estrazione dei file compressi.
        # Viene riutilizzata per ogni iterazione.
        cartella_tmp = os.path.join(cartella_regione_grezzi, "tmp_extract")
        os.makedirs(cartella_tmp, exist_ok=True)

        # Estrazione del contenuto ZIP
        with zipfile.ZipFile(percorso_file, "r") as archivio_zip:
            archivio_zip.extractall(cartella_tmp)

        file_estratti = os.listdir(cartella_tmp)

        file_istantaneo = None
        file_accumulato = None
        file_onde = None

        # Identificazione dei file in base allo stepType ERA5:
        # - instant → variabili istantanee (vento, temperatura, ecc.)
        # - accum → variabili cumulative (precipitazione)
        # - wave → variabili ondose
        for nome in file_estratti:

            if "stepType-instant" in nome and "wave" not in nome:
                file_istantaneo = nome

            elif "stepType-accum" in nome:
                file_accumulato = nome

            elif "wave" in nome and "stepType-instant" in nome:
                file_onde = nome

        # Verifica presenza dati meteorologici
        if file_istantaneo is None or file_accumulato is None:
            print("File meteo mancanti")
            continue

        # Verifica presenza dati ondosi
        if file_onde is None:
            print("File onde mancante")
            continue

        percorso_istantaneo = os.path.join(cartella_tmp, file_istantaneo)
        percorso_accumulato = os.path.join(cartella_tmp, file_accumulato)
        percorso_onde = os.path.join(cartella_tmp, file_onde)

        # Apertura dataset
        dataset_istantaneo = xr.open_dataset(percorso_istantaneo)
        dataset_accumulato = xr.open_dataset(percorso_accumulato)

        # Rinominazione della precipitazione totale (tp) in tp_hourly.
        # Scelta giustificata dal voler rendere esplicita la natura oraria
        # della variabile
        if "tp" in dataset_accumulato.data_vars:
            dataset_accumulato = dataset_accumulato.rename({"tp": "tp_hourly"})

        # Allineamento temporale e spaziale tra dataset accumulato e istantaneo.
        # Necessario per garantire coerenza nelle operazioni di merge.
        dataset_accumulato = dataset_accumulato.reindex_like(dataset_istantaneo)

        # Merge delle variabili meteorologiche
        dataset_meteo = xr.merge([dataset_istantaneo, dataset_accumulato])

        # Apertura dataset onde (gestito separatamente)
        dataset_onde = xr.open_dataset(percorso_onde)

        nome_base = nome_file.replace(".nc", "").replace(".zip", "")

        file_nc_meteo = os.path.join(cartella_meteo, f"{nome_base}_meteo.nc")
        file_nc_onde = os.path.join(cartella_onde, f"{nome_base}_onde.nc")

        file_csv_meteo = file_nc_meteo.replace(".nc", ".csv")
        file_csv_onde = file_nc_onde.replace(".nc", ".csv")

        # Salvataggio in formato NetCDF (formato principale per la pipeline)
        dataset_meteo.to_netcdf(file_nc_meteo)
        dataset_onde.to_netcdf(file_nc_onde)

        # Conversione opzionale in CSV per ispezione e debug
        dataset_csv_meteo = forza_datetime_per_csv(dataset_meteo)
        dataset_csv_onde = forza_datetime_per_csv(dataset_onde)

        dataset_csv_meteo.to_dataframe().reset_index().to_csv(file_csv_meteo, index=False)
        dataset_csv_onde.to_dataframe().reset_index().to_csv(file_csv_onde, index=False)

        print("Creati:", file_nc_meteo)
        print("Creati:", file_nc_onde)

        # Chiusura esplicita dei dataset per liberare memoria
        dataset_istantaneo.close()
        dataset_accumulato.close()
        dataset_meteo.close()
        dataset_onde.close()

        # Pulizia memoria
        del dataset_istantaneo, dataset_accumulato, dataset_meteo, dataset_onde
        gc.collect()

        # Pausa per evitare sovraccarico I/O
        time.sleep(1)

        # Pulizia cartella temporanea
        for f in os.listdir(cartella_tmp):
            try:
                os.remove(os.path.join(cartella_tmp, f))
            except:
                pass

print("\nUnzip e merge completati per tutte le regioni")
