import os
import xarray as xr
import pandas as pd


# Cartelle principali del progetto.
# Si lavora sul dataset regionale già costruito per applicare una maschera
# che distingua le celle marine da quelle terrestri.
cartella_radice = "dataset_intero"
cartella_preprocessing = os.path.join(cartella_radice, "preparazione_dati", "preprocessing")


def formatta_tempo_per_csv(dataset, nome_tempo="valid_time"):
    # Converte il tempo in formato leggibile per il CSV (data + ora).
    # Utile per evitare perdita di informazione temporale nell'esportazione.
    if nome_tempo in dataset.coords:
        dataset = dataset.copy()
        dataset[nome_tempo] = dataset[nome_tempo].dt.strftime("%Y-%m-%d %H:%M:%S")
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

    # Dataset di input (già unificato meteo + onde)
    percorso_input = os.path.join(cartella_regione, "dataset_regionale_unita.nc")

    # Dataset di output (con maschera mare applicata)
    percorso_output = os.path.join(cartella_regione, "dataset_regionale_unita.nc")

    # CSV di controllo per validazione qualitativa
    percorso_csv = os.path.join(cartella_regione, "dataset_regionale_mask_sample.csv")

    # Verifica esistenza dataset
    if not os.path.isfile(percorso_input):
        print("Dataset di input non trovato, salto regione")
        continue

    print("Apertura dataset")

    # Apertura lazy con chunk automatici
    # (i dati non vengono caricati completamente in memoria)
    dataset = xr.open_dataset(percorso_input, chunks="auto")

    # Dimensioni del dataset
    dim_tempo = dataset.sizes.get("valid_time", 1)
    dim_latitudine = dataset.sizes.get("latitude", 1)
    dim_longitudine = dataset.sizes.get("longitude", 1)

    # Definizione chunk manuali per ottimizzare memoria e I/O
    chunk_tempo = min(500, dim_tempo)
    chunk_latitudine = min(50, dim_latitudine)
    chunk_longitudine = min(50, dim_longitudine)

    dataset = dataset.chunk({
        "valid_time": chunk_tempo,
        "latitude": chunk_latitudine,
        "longitude": chunk_longitudine
    })

    # Verifica presenza della variabile chiave per identificare il mare
    # swh (altezza significativa delle onde) è assente sulle terre
    if "swh" not in dataset.data_vars:
        print("Variabile swh non presente, impossibile creare maschera")
        dataset.close()
        continue

    print("Calcolo percentuale valori mancanti nel tempo")

    # Calcolo della percentuale di NaN lungo la dimensione temporale
    # per ogni cella della griglia.
    # Le celle terrestri risultano quasi sempre prive di dati (NaN).
    percentuale_nan = dataset["swh"].isnull().mean(dim="valid_time")

    # Definizione soglia:
    # se una cella è NaN per oltre il 99% del tempo, allora è considerata non marina
    soglia_nan = 0.99
    maschera_mare = percentuale_nan < soglia_nan

    print("Applicazione maschera mare")

    # Applicazione della maschera:
    # mantiene solo le celle considerate marine
    dataset_mare = dataset.where(maschera_mare)

    # Riapplicazione chunk per mantenere efficienza
    dataset_mare = dataset_mare.chunk({
        "valid_time": chunk_tempo,
        "latitude": chunk_latitudine,
        "longitude": chunk_longitudine
    })

    print("Pulizia encoding variabili")

    # Rimozione encoding precedente per evitare conflitti in scrittura NetCDF
    for variabile in list(dataset_mare.data_vars) + list(dataset_mare.coords):
        dataset_mare[variabile].encoding = {}

    print("Salvataggio dataset filtrato")

    # Compressione dei dati per ridurre lo spazio su disco
    # mantenendo un buon compromesso tra dimensione e prestazioni
    encoding = {
        variabile: {
            "zlib": True,
            "complevel": 4,
            "chunksizes": (chunk_tempo, chunk_latitudine, chunk_longitudine)
        }
        for variabile in dataset_mare.data_vars
    }

    dataset_mare.to_netcdf(
        percorso_output,
        engine="netcdf4",
        encoding=encoding
    )

    print("Dataset salvato:", percorso_output)

    print("Creazione CSV di controllo (solo primo timestep)")

    # Estrazione di un singolo timestep per verifica manuale
    dataset_sample = dataset_mare.isel(valid_time=0).compute()

    dataset_csv = formatta_tempo_per_csv(dataset_sample)

    dataframe = dataset_csv.to_dataframe().reset_index()

    dataframe.to_csv(
        percorso_csv,
        sep=";",
        decimal=".",
        index=False
    )

    print("CSV creato:", percorso_csv)

    dataset.close()
    dataset_mare.close()


print("\nMaschera mare/terra completata")
