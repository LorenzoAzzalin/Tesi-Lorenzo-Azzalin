import xarray as xr
import numpy as np
import pandas as pd
import os

# Cartelle principali della pipeline.
# Si parte dai dataset preprocessati e si generano nuove feature
# utili per migliorare la capacità predittiva dei modelli.
cartella_radice = "dataset_intero"
cartella_preprocessing = os.path.join(cartella_radice, "preparazione_dati", "preprocessing")
cartella_output = os.path.join(cartella_radice, "preparazione_dati", "feature_engineering")

os.makedirs(cartella_output, exist_ok=True)

# Individuazione automatica delle regioni disponibili
regioni = [
    nome for nome in os.listdir(cartella_preprocessing)
    if os.path.isdir(os.path.join(cartella_preprocessing, nome))
]

print("Regioni trovate:", regioni)

# Loop su tutte le regioni
for regione in regioni:

    print("\nElaborazione feature engineering per regione:", regione)

    # Dataset di input: dopo preprocessing e conversione unità
    percorso_input = os.path.join(
        cartella_preprocessing,
        regione,
        "dataset_regionale_unita.nc"
    )

    if not os.path.isfile(percorso_input):
        print("Dataset non trovato, regione saltata")
        continue

    print("Apertura dataset:", percorso_input)

    dataset = xr.open_dataset(percorso_input)

    # Chunking per gestire dataset di grandi dimensioni.
    # Consente di lavorare in modalità lazy senza saturare la memoria RAM.
    dataset = dataset.chunk({
        "valid_time": 500,
        "latitude": 50,
        "longitude": 50
    })

    print("Dimensioni dataset:", dataset.sizes)
    print("Variabili presenti:", list(dataset.data_vars))

    # La direzione delle onde (mwd) è una variabile angolare.
    # Viene trasformata in componenti seno e coseno per:
    # - evitare discontinuità (0° ≈ 360°)
    # - facilitare l'apprendimento da parte del modello
    if "mwd" in dataset.data_vars:
        print("Trasformazione mwd in sin e cos")

        angolo = np.deg2rad(dataset["mwd"])
        dataset["mwd_sin"] = np.sin(angolo)
        dataset["mwd_cos"] = np.cos(angolo)

        dataset = dataset.drop_vars("mwd")
    else:
        print("Variabile mwd non presente")

    # Queste feature aiutano il modello a catturare la ciclicità giornaliera (hour)
    # e la stagionalità (month)
    print("Creazione feature temporali")

    dataset["hour"] = dataset["valid_time"].dt.hour
    dataset["month"] = dataset["valid_time"].dt.month

    # Il modello può osservare lo stato del sistema nelle ore precedenti.
    print("Creazione variabili di lag")

    variabili_lag = [
    "swh",
    "u10",
    "v10",
    "msl",
    "t2m",
    "sst",
    "tcc",
    "tp_hourly"
    ]
    
    lag_temporali = [1, 3]

    for variabile in variabili_lag:

        if variabile not in dataset.data_vars:
            print(f"{variabile} non presente")
            continue

        for lag in lag_temporali:
            nome_lag = f"{variabile}_lag_{lag}"
            print("Creazione:", nome_lag)

            # Lo shift introduce valori NaN nelle prime posizioni temporali.
            # Questi verranno gestiti successivamente durante il training.
            dataset[nome_lag] = dataset[variabile].shift(
                valid_time=lag,
                fill_value=np.nan
            )

    print("Variabili di lag create correttamente")

    # Reset encoding per evitare problemi nella scrittura NetCDF
    for variabile in list(dataset.data_vars) + list(dataset.coords):
        dataset[variabile].encoding = {}

    # Creazione cartella output
    cartella_regione_output = os.path.join(cartella_output, regione)
    os.makedirs(cartella_regione_output, exist_ok=True)

    file_output_nc = os.path.join(
        cartella_regione_output,
        "dataset_feature_engineered.nc"
    )

    print("Salvataggio dataset NetCDF")

    dataset.to_netcdf(file_output_nc)

    print("Dataset salvato in:", file_output_nc)

    # Creazione CSV di controllo (solo primo timestep)
    # utile per validazione e verifica manuale
    print("Creazione CSV di controllo")

    dataset_campione = dataset.isel(valid_time=0)

    dataframe = dataset_campione.to_dataframe().reset_index()

    dataframe["valid_time"] = pd.to_datetime(
        dataframe["valid_time"]
    ).dt.strftime("%Y-%m-%d %H:%M:%S")

    file_output_csv = os.path.join(
        cartella_regione_output,
        "dataset_feature_engineered_sample.csv"
    )

    dataframe.to_csv(
        file_output_csv,
        sep=";",
        decimal=".",
        index=False
    )

    print("CSV salvato in:", file_output_csv)

    dataset.close()

print("\nFeature engineering step 1 completato")
