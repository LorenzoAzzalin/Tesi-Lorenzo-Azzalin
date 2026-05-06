import xarray as xr
import numpy as np
import os

cartella_root = r"C:\Users\loren\Desktop\progetto_ml\dataset_intero\preparazione_dati\preprocessing"

regioni = os.listdir(cartella_root)

for regione in regioni:

    percorso_file = os.path.join(
        cartella_root,
        regione,
        "dataset_pulito",
        "dataset_regionale_pulito.nc"
    )

    if not os.path.exists(percorso_file):
        print(f"\nFile non trovato per la regione {regione}, salto...")
        continue

    print(f"\nAnalisi regione: {regione}")

    dataset = xr.open_dataset(percorso_file)

    print("\nDimensioni del dataset:")
    print(dataset.sizes)

    print("\nTipo delle variabili:")
    for variabile in dataset.data_vars:
        print(variabile, dataset[variabile].dtype)

    print("\nControllo percentuale NaN per swh:")

    variabile_target = "swh"

    if variabile_target not in dataset:
        print("Variabile swh non presente, salto controllo NaN")
    else:
        dati = dataset[variabile_target]

        # ==============================
        # ✔ Calcolo NaN robusto (chunked)
        # ==============================

        nan_totali = float(
            dati.isnull()
            .mean(dim=["valid_time", "latitude", "longitude"])
            .compute() * 100
        )

        print("Percentuale NaN totale:", nan_totali)

        percentuale_nan_temporale = dati.isnull().mean(dim="valid_time")

        maschera_terra = percentuale_nan_temporale > 0.99
        maschera_mare = ~maschera_terra

        nan_mare = float(
            dati.where(maschera_mare)
            .isnull()
            .mean(dim=["valid_time", "latitude", "longitude"])
            .compute() * 100
        )

        print("Percentuale NaN sul mare:", nan_mare)

    print("\nControllo range dei valori fisici:")

    variabili_da_controllare = ["swh", "u10", "t2m", "msl"]

    for variabile in variabili_da_controllare:
        if variabile not in dataset:
            print(f"{variabile} non presente nel dataset")
            continue

        dati = dataset[variabile]

        minimo = float(dati.min().compute())
        massimo = float(dati.max().compute())

        print(f"{variabile} -> min: {minimo}, max: {massimo}")

    print("\nControllo continuità temporale:")

    if "valid_time" not in dataset:
        print("Variabile temporale non presente")
    else:
        tempo = dataset.valid_time.values

        differenze = np.diff(tempo).astype("timedelta64[h]").astype(int)

        print("Intervallo minimo (ore):", differenze.min())
        print("Intervallo massimo (ore):", differenze.max())
