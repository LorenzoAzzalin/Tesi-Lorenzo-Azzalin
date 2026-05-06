import os
import xarray as xr
import numpy as np
import json

cartella_radice = "dataset_intero"

cartella_dati = os.path.join(
    cartella_radice,
    "preparazione_dati",
    "dataset_pronto_dl"
)

regioni = [
    nome for nome in os.listdir(cartella_dati)
    if os.path.isdir(os.path.join(cartella_dati, nome))
]

print("Regioni trovate:", regioni)


# Funzione per applicare lo scaling
# Ogni variabile viene standardizzata utilizzando i parametri
# calcolati esclusivamente sul dataset di training
def applica_scaling(dataset, scaler):

    for variabile in scaler:

        if variabile not in dataset.data_vars:
            continue

        media = scaler[variabile]["mean"]
        deviazione_standard = scaler[variabile]["std"]

        # Evita divisione per zero (caso raro ma possibile)
        if deviazione_standard == 0:
            continue

        # Standardizzazione: (x - media) / std
        # I valori NaN vengono mantenuti invariati
        dataset[variabile] = (dataset[variabile] - media) / deviazione_standard

    return dataset


# Funzione per costruire encoding ottimizzato per NetCDF
# Consente compressione e gestione efficiente della memoria
def costruisci_encoding(dataset):

    encoding = {}

    dim_t = dataset.sizes["valid_time"]
    dim_lat = dataset.sizes["latitude"]
    dim_lon = dataset.sizes["longitude"]

    chunk_t = min(500, dim_t)
    chunk_lat = min(50, dim_lat)
    chunk_lon = min(50, dim_lon)

    for var in dataset.data_vars:

        dims = dataset[var].dims

        if dims == ("valid_time", "latitude", "longitude"):
            encoding[var] = {
                "zlib": True,
                "complevel": 4,
                "chunksizes": (chunk_t, chunk_lat, chunk_lon)
            }

        elif dims == ("valid_time",):
            encoding[var] = {
                "zlib": True,
                "complevel": 4,
                "chunksizes": (chunk_t,)
            }

        else:
            encoding[var] = {
                "zlib": True,
                "complevel": 4
            }

    return encoding


# Ciclo su tutte le regioni
for i, regione in enumerate(regioni):

    print("\nApplicazione scaler per regione:", regione, f"({i+1}/{len(regioni)})")

    cartella_regione = os.path.join(cartella_dati, regione)

    # Caricamento dello scaler (calcolato sul training set)
    percorso_scaler = os.path.join(cartella_regione, "scaler.json")

    if not os.path.isfile(percorso_scaler):
        print("Scaler non trovato, salto regione")
        continue

    with open(percorso_scaler, "r") as f:
        scaler = json.load(f)

    # Lo stesso scaler viene applicato a train, validation e test
    dataset_file = {
        "train": "era5_train.nc",
        "validation": "era5_val.nc",
        "test": "era5_test.nc"
    }

    for tipo, nome_file in dataset_file.items():

        percorso_input = os.path.join(cartella_regione, nome_file)

        if not os.path.isfile(percorso_input):
            print("File non trovato:", percorso_input)
            continue

        percorso_output = os.path.join(
            cartella_regione,
            nome_file.replace(".nc", "_scalato.nc")
        )

        # Evita ricalcolo se il file scalato esiste già
        if os.path.isfile(percorso_output):
            print(nome_file, "già scalato, salto")
            continue

        print("Scaling:", nome_file)

        dataset = xr.open_dataset(percorso_input)

        # Chunking per lavorare su dataset di grandi dimensioni
        dataset = dataset.chunk({
            "valid_time": 500,
            "latitude": 50,
            "longitude": 50
        })

        # Applicazione dello scaling
        dataset_scalato = applica_scaling(dataset, scaler)

        # Definizione encoding temporale
        dataset_scalato["valid_time"].encoding = {
            "units": "hours since 1970-01-01",
            "dtype": "float64"
        }

        # Reset encoding variabili per evitare problemi di scrittura
        for var in dataset_scalato.data_vars:
            dataset_scalato[var].encoding = {}

        print("Salvataggio:", percorso_output)

        dataset_scalato.to_netcdf(
            percorso_output,
            encoding=costruisci_encoding(dataset_scalato)
        )

        dataset.close()
        dataset_scalato.close()


print("\nScaling completato per tutte le regioni")
