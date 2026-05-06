import xarray as xr
import os


cartella_dati = "dataset_intero/preparazione_dati/dataset_pronto_dl"

regioni = [
    nome for nome in os.listdir(cartella_dati)
    if os.path.isdir(os.path.join(cartella_dati, nome))
]

print("Regioni trovate:", regioni)


variabili = ["u10", "t2m", "msl", "swh"]

numero_campioni = 1000


for regione in regioni:

    print("\nControllo regione:", regione)

    percorso_file = os.path.join(
        cartella_dati,
        regione,
        "era5_train_scalato.nc"
    )

    if not os.path.isfile(percorso_file):
        print("File scalato non trovato, salto regione")
        continue

    print("Apertura dataset:", percorso_file)

    dataset = xr.open_dataset(percorso_file)

    # Campionamento per evitare problemi di memoria
    dataset_campione = dataset.isel(valid_time=slice(0, numero_campioni))

    for variabile in variabili:

        if variabile not in dataset_campione.data_vars:
            continue

        dati = dataset_campione[variabile]

        media = float(dati.mean().compute())
        std = float(dati.std().compute())
        nan = float(dati.isnull().mean().compute() * 100)

        print(f"{variabile}: mean={media:.3f}, std={std:.3f}, NaN={nan:.2f}%")

    dataset.close()


print("\nControllo completato")
