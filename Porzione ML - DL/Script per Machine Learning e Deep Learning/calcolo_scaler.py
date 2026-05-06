import xarray as xr
import numpy as np
import os
import json

cartella_radice = "dataset_intero"

# Percorso dei dati già pronti per il Deep Learning 
cartella_dati_dl = os.path.join(
    cartella_radice,
    "preparazione_dati",
    "dataset_pronto_dl"
)


# Individuazione automatica delle regioni disponibili
regioni = [
    nome for nome in os.listdir(cartella_dati_dl)
    if os.path.isdir(os.path.join(cartella_dati_dl, nome))
]

print("Regioni trovate:", regioni)


# Variabili su cui calcolare media e deviazione standard.
# Si includono sia variabili originali sia feature derivate (cicliche, direzionali).
variabili = [
    "pp1d", "u10", "v10",
    "t2m", "msl", "sst",
    "tcc", "tp_hourly",
    "mwd_sin", "mwd_cos",
    "hour_sin", "hour_cos",
    "month_sin", "month_cos"
]


# Ciclo su tutte le regioni
for indice, regione in enumerate(regioni):

    print("\nCalcolo scaler per regione:", regione, f"({indice + 1}/{len(regioni)})")

    # Lo scaling viene calcolato solo sul training set per evitare data leakage
    percorso_train = os.path.join(
        cartella_dati_dl,
        regione,
        "era5_train.nc"
    )

    # Controllo esistenza file
    if not os.path.isfile(percorso_train):
        print("Dataset di training non trovato, salto regione")
        continue

    print("Apertura dataset:", percorso_train)

    dataset = xr.open_dataset(percorso_train)

    # Suddivisione in chunk per lavorare in modalità lazy
    # evitando il caricamento completo in memoria
    dataset = dataset.chunk({
        "valid_time": 500,
        "latitude": 50,
        "longitude": 50
    })

    scaler = {}

    # Calcolo media e deviazione standard per ogni variabile
    for variabile in variabili:

        if variabile not in dataset.data_vars:
            print(f"{variabile} non presente, salto")
            continue

        print(f"Calcolo media e deviazione standard per: {variabile}")

        dati = dataset[variabile]

        # Calcolo lazy con Dask:
        # i dati vengono elaborati a blocchi senza essere caricati interamente in RAM
        media = dati.mean().compute()
        deviazione_standard = dati.std().compute()

        media = float(media)
        deviazione_standard = float(deviazione_standard)

        print(f"{variabile:15s} media={media:.3f}  std={deviazione_standard:.3f}")

        # Salvataggio dei parametri dello scaler
        scaler[variabile] = {
            "mean": media,
            "std": deviazione_standard
        }

    # Salvataggio dello scaler in formato JSON
    # Questo file verrà utilizzato per applicare la stessa trasformazione
    # ai dataset di validation e test
    percorso_scaler = os.path.join(
        cartella_dati_dl,
        regione,
        "scaler.json"
    )

    with open(percorso_scaler, "w") as file_json:
        json.dump(scaler, file_json, indent=4)

    print("Scaler salvato in:", percorso_scaler)

    dataset.close()


print("\nCalcolo scaler completato")
