import xarray as xr
import numpy as np
import os
import pandas as pd

# Cartella principale del progetto
cartella_principale = "dataset_intero"

# Cartella contenente i dataset dopo il primo step di feature engineering
cartella_feature = os.path.join(cartella_principale, "preparazione_dati", "feature_engineering")

# Individuazione automatica delle regioni disponibili
regioni = [
    nome for nome in os.listdir(cartella_feature)
    if os.path.isdir(os.path.join(cartella_feature, nome))
]

print("Regioni individuate:", regioni)

# Elaborazione per ciascuna regione
for regione in regioni:

    print("\nElaborazione feature cicliche per la regione:", regione)

    # Percorsi dei file
    percorso_input = os.path.join(
        cartella_feature,
        regione,
        "dataset_feature_engineered.nc"
    )

    percorso_output = os.path.join(
        cartella_feature,
        regione,
        "dataset_feature_engineered_ciclico.nc"
    )

    percorso_csv = os.path.join(
        cartella_feature,
        regione,
        "dataset_feature_engineered_ciclico_sample.csv"
    )

    # Controllo presenza file di output (evita rielaborazioni inutili)
    if os.path.isfile(percorso_output):
        dimensione_mb = os.path.getsize(percorso_output) / (1024 * 1024)

        if dimensione_mb > 50:
            print(f"File già presente ({dimensione_mb:.1f} MB), salto della regione")
            continue
        else:
            print("File presente ma incompleto, rigenerazione")

    # Controllo presenza file di input
    if not os.path.isfile(percorso_input):
        print("File di input non trovato, regione saltata")
        continue

    print("Apertura dataset:", percorso_input)

    dataset = xr.open_dataset(percorso_input)

    # Definizione dei chunk per gestire dataset di grandi dimensioni.
    # Consente di lavorare in modalità lazy senza saturare la memoria.
    dimensione_tempo = dataset.sizes["valid_time"]
    dimensione_lat = dataset.sizes["latitude"]
    dimensione_lon = dataset.sizes["longitude"]

    chunk_tempo = min(500, dimensione_tempo)
    chunk_lat = min(50, dimensione_lat)
    chunk_lon = min(50, dimensione_lon)

    dataset = dataset.chunk({
        "valid_time": chunk_tempo,
        "latitude": chunk_lat,
        "longitude": chunk_lon
    })

    print("Dimensioni dataset:", dataset.sizes)

    # Le variabili temporali (ora e mese) sono grandezze periodiche.
    # La trasformazione seno/coseno permette di mantenere la continuità ed
    # evitare discontinuità per il modello
    if "hour" in dataset:
        print("Creazione variabili cicliche per l'ora")
        dataset["hour_sin"] = np.sin(2 * np.pi * dataset["hour"] / 24)
        dataset["hour_cos"] = np.cos(2 * np.pi * dataset["hour"] / 24)

    if "month" in dataset:
        print("Creazione variabili cicliche per il mese")
        dataset["month_sin"] = np.sin(2 * np.pi * dataset["month"] / 12)
        dataset["month_cos"] = np.cos(2 * np.pi * dataset["month"] / 12)

    # Rimozione delle variabili temporali originali
    # (sostituite dalle rappresentazioni cicliche più informative)
    dataset = dataset.drop_vars(
        [v for v in ["hour", "month"] if v in dataset.data_vars]
    )

    # Reset encoding per evitare problemi durante il salvataggio
    for variabile in dataset.data_vars:
        dataset[variabile].encoding = {}

    # Definizione esplicita del formato temporale
    dataset["valid_time"].encoding = {
        "units": "hours since 1970-01-01",
        "dtype": "float64"
    }

    # Configurazione encoding con compressione
    # Riduce lo spazio su disco e migliora le prestazioni di I/O
    encoding = {}

    for variabile in dataset.data_vars:

        dimensioni = dataset[variabile].dims

        if dimensioni == ("valid_time", "latitude", "longitude"):
            encoding[variabile] = {
                "zlib": True,
                "complevel": 4,
                "chunksizes": (chunk_tempo, chunk_lat, chunk_lon)
            }

        elif dimensioni == ("valid_time",):
            encoding[variabile] = {
                "zlib": True,
                "complevel": 4,
                "chunksizes": (chunk_tempo,)
            }

        else:
            encoding[variabile] = {
                "zlib": True,
                "complevel": 4
            }

    print("Salvataggio dataset NetCDF")

    dataset.to_netcdf(
        percorso_output,
        encoding=encoding
    )

    print("Dataset salvato in:", percorso_output)

    # Creazione CSV di controllo (solo un timestep)
    # utile per validazione qualitativa
    print("Creazione file CSV di controllo")

    dataset_campione = dataset.isel(valid_time=0).compute()

    dataframe = dataset_campione.to_dataframe().reset_index()

    dataframe["valid_time"] = pd.to_datetime(dataframe["valid_time"])

    dataframe.to_csv(
        percorso_csv,
        sep=";",
        decimal=".",
        index=False
    )

    print("CSV salvato in:", percorso_csv)

    dataset.close()

print("\nStep 2 feature engineering completato")
