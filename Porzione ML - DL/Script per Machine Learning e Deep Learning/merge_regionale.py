import os
import xarray as xr
import pandas as pd
import gc
import shutil

# Percorsi della pipeline:
# si lavora sui dati già preprocessati per costruire un dataset regionale unificato
cartella_radice = "dataset_intero"
cartella_preprocessing = os.path.join(cartella_radice, "preparazione_dati", "preprocessing")


def forza_datetime_per_csv(dataset, nome_tempo="valid_time"):
    # Converte il tempo in stringa completa per evitare perdita dell'ora nel CSV.
    # Questo è necessario perché alcune esportazioni possono perdere la componente temporale.
    if nome_tempo in dataset.coords:
        dataset = dataset.copy()
        dataset[nome_tempo] = dataset[nome_tempo].dt.strftime("%Y-%m-%d %H:%M:%S")
    return dataset


def rimuovi_variabili_problematiche(dataset):
    # Rimuove variabili non compatibili con la serializzazione NetCDF
    # o non utili per la modellazione.
    # In particolare:
    # - variabili con dtype "object" (non numeriche)
    # - "expver" (variabile tecnica ERA5)
    # - eventuale variabile "regione"
    variabili_da_rimuovere = []

    for variabile in dataset.variables:
        if dataset[variabile].dtype == "object":
            variabili_da_rimuovere.append(variabile)

    if "expver" in dataset.variables:
        variabili_da_rimuovere.append("expver")

    if "regione" in dataset.variables:
        variabili_da_rimuovere.append("regione")

    if variabili_da_rimuovere:
        print("Rimozione variabili problematiche:", variabili_da_rimuovere)
        dataset = dataset.drop_vars(variabili_da_rimuovere)

    return dataset


# Individuazione automatica delle regioni disponibili
regioni = [
    nome for nome in os.listdir(cartella_preprocessing)
    if os.path.isdir(os.path.join(cartella_preprocessing, nome))
]

print("Regioni trovate:", regioni)


for regione in regioni:

    print("\nElaborazione regione:", regione)

    cartella_regione = os.path.join(cartella_preprocessing, regione)
    cartella_meteo = os.path.join(cartella_regione, "meteo")
    cartella_onde = os.path.join(cartella_regione, "onde")
    cartella_temporanei = os.path.join(cartella_regione, "temporanei")

    # Output finale: dataset regionale completo (tutti i mesi concatenati)
    percorso_output = os.path.join(cartella_regione, "dataset_regionale.nc")

    # Salta la regione se il file finale esiste già
    if os.path.exists(percorso_output):
        print("File finale già presente, salto regione")
        continue

    os.makedirs(cartella_temporanei, exist_ok=True)

    # Lista dei file meteo (uno per mese)
    file_meteo = sorted([
        f for f in os.listdir(cartella_meteo)
        if f.endswith("_meteo.nc")
    ])

    if len(file_meteo) == 0:
        print("Nessun file meteo trovato")
        continue

    # Per ogni unisce meteo + onde e poi salva un file temporaneo
    for nome_file in file_meteo:

        nome_base = nome_file.replace("_meteo.nc", "")

        percorso_meteo = os.path.join(cartella_meteo, nome_file)
        percorso_onde = os.path.join(cartella_onde, f"{nome_base}_onde_allineate.nc")

        print("\nMerge mensile:", nome_base)

        if not os.path.exists(percorso_onde):
            print("File onde allineate mancante:", nome_base)
            continue

        percorso_temp = os.path.join(cartella_temporanei, f"{nome_base}_finale.nc")

        # Controllo integrità file temporaneo
        # Se esiste ma è corrotto viene rigenerato
        if os.path.exists(percorso_temp):
            try:
                xr.open_dataset(percorso_temp).close()
                print("File già valido, salto")
                continue
            except:
                print("File corrotto, rigenero")
                os.remove(percorso_temp)

        try:
            ds_meteo = xr.open_dataset(percorso_meteo)
            ds_onde = xr.open_dataset(percorso_onde)

            # Merge delle variabili meteo e onde (stessa griglia dopo regridding)
            ds = xr.merge([ds_meteo, ds_onde])
            ds = rimuovi_variabili_problematiche(ds)

            # Conversione a float32 per ridurre l'uso di memoria
            ds = ds.astype("float32")

            ds.to_netcdf(percorso_temp)

            ds_meteo.close()
            ds_onde.close()
            ds.close()

            del ds
            gc.collect()

        except Exception as e:
            print("Errore nel merge mensile:", nome_base, e)
            continue

    # Raccolta dei file temporanei generati (uno per mese)
    file_temporanei = sorted([
        os.path.join(cartella_temporanei, f)
        for f in os.listdir(cartella_temporanei)
        if f.endswith("_finale.nc")
    ])

    if len(file_temporanei) == 0:
        print("Nessun file temporaneo disponibile")
        continue

    print("\nUnione temporale della regione:", regione)

    try:
        # Apertura lazy con chunk sul tempo:
        # - evita il caricamento completo in memoria
        # - consente di gestire dataset di grandi dimensioni
        dataset = xr.open_mfdataset(
            file_temporanei,
            combine="nested",
            concat_dim="valid_time",
            parallel=True,
            chunks={"valid_time": 1000}
        )

        # Ordinamento temporale
        dataset = dataset.sortby("valid_time")
        dataset = rimuovi_variabili_problematiche(dataset)

        print("Dataset pronto, dimensioni:", dataset.sizes)

        print("Salvataggio dataset finale")

        dataset.to_netcdf(
            percorso_output,
            engine="netcdf4"
        )

        dataset.close()
        del dataset
        gc.collect()

        print("Dataset regionale creato")

    except Exception as e:
        print("Errore nella regione:", regione, e)
        continue

    # Creazione CSV di esempio (primo timestep)
    # utile per validazione e ispezione manuale
    try:
        ds = xr.open_dataset(percorso_output)
        ds_csv = forza_datetime_per_csv(ds)

        df = ds_csv.isel(valid_time=0).to_dataframe().reset_index()

        percorso_csv = os.path.join(cartella_regione, "dataset_regionale_sample.csv")
        df.to_csv(percorso_csv, sep=";", decimal=".", index=False)

        print("CSV creato:", percorso_csv)

        ds.close()

    except Exception as e:
        print("Errore creazione CSV:", e)

    # Eliminazione dei file temporanei
    # per liberare spazio disco dopo la creazione del dataset finale
    try:
        print("Eliminazione temporanei")

        gc.collect()

        shutil.rmtree(cartella_temporanei)

        print("Temporanei eliminati")

    except Exception as e:
        print("Errore eliminazione:", e)


print("\nMerge completato")
