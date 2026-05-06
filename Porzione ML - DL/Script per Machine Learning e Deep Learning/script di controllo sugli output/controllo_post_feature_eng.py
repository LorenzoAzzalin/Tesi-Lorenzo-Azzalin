import os
import xarray as xr
import numpy as np


cartella_feature = "dataset_intero/preparazione_dati/feature_engineering"

regioni = [
    nome for nome in os.listdir(cartella_feature)
    if os.path.isdir(os.path.join(cartella_feature, nome))
]

print("Regioni trovate:", regioni)


for regione in regioni:

    print("\nAnalisi regione:", regione)

    percorso_dataset = os.path.join(
        cartella_feature,
        regione,
        "dataset_feature_engineered_ciclico.nc"
    )

    if not os.path.isfile(percorso_dataset):
        print("Dataset non trovato, salto regione")
        continue

    print("Apertura dataset")
    dataset = xr.open_dataset(percorso_dataset, chunks="auto")

    # Controllo dimensioni e struttura generale
    print("\nDimensioni dataset:")
    print(dataset.sizes)

    print("\nNumero variabili:", len(dataset.data_vars))

    # Verifica presenza variabili chiave
    print("\nControllo variabili chiave")

    variabili_attese = [
        "mwd_sin", "mwd_cos",
        "hour_sin", "hour_cos",
        "month_sin", "month_cos"
    ]

    for var in variabili_attese:
        if var in dataset.data_vars:
            print(var, "OK")
        else:
            print(var, "MANCANTE")

    # Verifica presenza variabili di lag
    print("\nControllo variabili di lag")

    variabili_lag = [v for v in dataset.data_vars if "lag" in v]

    if len(variabili_lag) == 0:
        print("Nessuna variabile di lag trovata")
    else:
        print("Numero variabili di lag:", len(variabili_lag))
        print("Esempio:", variabili_lag[:5])

    # Controllo percentuale NaN su campione per evitare carichi eccessivi
    print("\nControllo NaN (campionato)")

    dataset_campione = dataset.isel(valid_time=slice(0, None, 200))

    for var in dataset_campione.data_vars:

        percentuale_nan = float(
            dataset_campione[var]
            .isnull()
            .mean()
            .compute() * 100
        )

        print(f"{var}: {percentuale_nan:.2f}%")

    # Controllo specifico dei NaN nelle variabili di lag
    print("\nControllo NaN nei lag")

    for var in variabili_lag[:5]:

        percentuale_nan = float(
            dataset_campione[var]
            .isnull()
            .mean()
            .compute() * 100
        )

        print(f"{var}: {percentuale_nan:.2f}%")

    # Verifica coerenza dimensionale tra le variabili
    print("\nControllo coerenza dimensionale")

    shape_riferimento = None
    errore_shape = False

    for var in dataset.data_vars:

        shape = dataset[var].shape

        if shape_riferimento is None:
            shape_riferimento = shape
        else:
            if shape != shape_riferimento:
                print("Errore shape:", var, shape)
                errore_shape = True

    if not errore_shape:
        print("Tutte le variabili hanno shape coerente")

    # Verifica range delle feature cicliche (devono stare tra -1 e 1)
    print("\nControllo range feature cicliche")

    for var in ["hour_sin", "hour_cos", "month_sin", "month_cos"]:

        if var in dataset:

            dati = dataset[var].isel(valid_time=slice(0, None, 200))

            minimo = float(dati.min().compute())
            massimo = float(dati.max().compute())

            print(f"{var}: min={minimo:.3f}, max={massimo:.3f}")

    # Controllo continuità temporale
    print("\nControllo timeline")

    tempo = dataset.valid_time.values

    if len(tempo) > 1:
        diff = np.diff(tempo).astype("timedelta64[h]").astype(int)
        print("Intervallo minimo:", diff.min())
        print("Intervallo massimo:", diff.max())

    dataset.close()


print("\nControllo feature engineering completato")
