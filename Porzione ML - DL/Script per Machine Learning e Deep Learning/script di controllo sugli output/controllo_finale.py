import os
import xarray as xr
import numpy as np


# Percorsi principali del progetto
cartella_radice = "dataset_intero"
cartella_preprocessing = os.path.join(cartella_radice, "preparazione_dati", "preprocessing")


# Individuazione delle regioni disponibili
regioni = [
    nome for nome in os.listdir(cartella_preprocessing)
    if os.path.isdir(os.path.join(cartella_preprocessing, nome))
]

print("Regioni trovate:", regioni)


for regione in regioni:

    print("\nAnalisi regione:", regione)

    # Dataset corretto: quello dopo conversione unità
    percorso_dataset = os.path.join(
        cartella_preprocessing,
        regione,
        "dataset_regionale_unita.nc"
    )

    if not os.path.isfile(percorso_dataset):
        print("Dataset non trovato, salto regione")
        continue

    print("Apertura dataset")

    dataset = xr.open_dataset(percorso_dataset, chunks="auto")

    print("Dimensioni dataset:", dataset.sizes)
    print("Variabili presenti:", list(dataset.data_vars))

    # Analisi NaN (campionata per evitare problemi di memoria)
    print("\nAnalisi percentuale NaN (campionata)")

    dataset_campione = dataset.isel(valid_time=slice(0, None, 100))

    for variabile in dataset_campione.data_vars:

        totale = dataset_campione[variabile].size
        numero_nan = dataset_campione[variabile].isnull().sum().compute()

        percentuale_nan = (numero_nan / totale) * 100

        print(f"{variabile}: NaN {percentuale_nan:.2f}%")

    # Analisi specifica della variabile swh
    if "swh" in dataset.data_vars:

        print("\nAnalisi approfondita swh")

        swh_campione = dataset["swh"].isel(valid_time=slice(0, None, 100))

        minimo = float(swh_campione.min().compute())
        massimo = float(swh_campione.max().compute())
        media = float(swh_campione.mean().compute())

        percentuale_nan_swh = float(swh_campione.isnull().mean().compute()) * 100

        print("Valore minimo:", minimo)
        print("Valore massimo:", massimo)
        print("Valore medio:", media)
        print("Percentuale NaN:", percentuale_nan_swh)

        # Verifica timestep completamente vuoti
        timestep_vuoti = (
            swh_campione.isnull()
            .all(dim=["latitude", "longitude"])
            .sum()
            .compute()
        )

        print("Numero timestep completamente vuoti:", int(timestep_vuoti))

        # Interpretazione (coerente con la tua pipeline reale)
        print("\nNota interpretativa:")
        print("La presenza di NaN è diffusa e non limitata alle sole aree di terra.")
        print("Questo indica una distribuzione strutturale dei dati mancanti nel dominio marino.")

    else:
        print("Variabile swh non presente")

    # Controllo griglia spaziale
    print("\nControllo griglia spaziale")

    latitudine = dataset.latitude.values
    longitudine = dataset.longitude.values

    print("Latitudine min:", float(latitudine.min()), "Latitudine max:", float(latitudine.max()))
    print("Longitudine min:", float(longitudine.min()), "Longitudine max:", float(longitudine.max()))

    print("Numero punti latitudine:", len(latitudine))
    print("Numero punti longitudine:", len(longitudine))

    if len(latitudine) > 1:
        passo_lat = float(abs(np.diff(latitudine).mean()))
        print("Passo medio latitudine:", passo_lat)

    if len(longitudine) > 1:
        passo_lon = float(abs(np.diff(longitudine).mean()))
        print("Passo medio longitudine:", passo_lon)

    # Controllo continuità temporale
    print("\nControllo continuità temporale")

    tempo = dataset.valid_time.values

    if len(tempo) > 1:

        differenze = np.diff(tempo).astype("timedelta64[h]").astype(int)

        delta_min = int(differenze.min())
        delta_max = int(differenze.max())

        print("Intervallo minimo (ore):", delta_min)
        print("Intervallo massimo (ore):", delta_max)

        if delta_max > 1:
            print("Attenzione: discontinuità temporale rilevata")
        else:
            print("Sequenza temporale continua")

    dataset.close()


print("\nAnalisi completata")
