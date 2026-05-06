import os
import xarray as xr


cartella_radice = "dataset_intero"
cartella_preprocessing = os.path.join(cartella_radice, "preparazione_dati", "preprocessing")


regioni = [
    nome for nome in os.listdir(cartella_preprocessing)
    if os.path.isdir(os.path.join(cartella_preprocessing, nome))
]

print("Regioni trovate:", regioni)


for regione in regioni:

    print("\nElaborazione regione:", regione)

    cartella_regione = os.path.join(cartella_preprocessing, regione)

    percorso_input = os.path.join(cartella_regione, "dataset_regionale.nc")
    percorso_output = os.path.join(cartella_regione, "dataset_regionale_unita.nc")

    # controllo esistenza dataset finale
    if os.path.isfile(percorso_output):
        dimensione_gb = os.path.getsize(percorso_output) / (1024 ** 3)

        if dimensione_gb > 5:
            print("File già presente e valido, salto regione")
            continue
        else:
            print("File presente ma troppo piccolo, rigenerazione")

    # controllo input
    if not os.path.isfile(percorso_input):
        print("Dataset regionale non trovato, salto")
        continue

    print("Apertura dataset")

    dataset = xr.open_dataset(percorso_input, chunks="auto")

    print("Variabili originali:", list(dataset.data_vars))

    # conversioni unità fisiche
    if "t2m" in dataset:
        dataset["t2m"] = dataset["t2m"] - 273.15
        dataset["t2m"].attrs["units"] = "degC"

    if "sst" in dataset:
        dataset["sst"] = dataset["sst"] - 273.15
        dataset["sst"].attrs["units"] = "degC"

    if "tp_hourly" in dataset:
        dataset["tp_hourly"] = dataset["tp_hourly"] * 1000.0
        dataset["tp_hourly"].attrs["units"] = "mm"

    if "msl" in dataset:
        dataset["msl"] = dataset["msl"] / 100.0
        dataset["msl"].attrs["units"] = "hPa"

    print("Variabili dopo conversione:", list(dataset.data_vars))

    # controllo variabili importanti
    if "swh" not in dataset.data_vars:
        print("Attenzione: variabile swh non presente")

    print("Salvataggio dataset con compressione")

    encoding = {
        variabile: {"zlib": True, "complevel": 4}
        for variabile in dataset.data_vars
    }

    dataset.to_netcdf(
        percorso_output,
        engine="netcdf4",
        encoding=encoding
    )

    dataset.close()

    print("Dataset convertito salvato:", percorso_output)


print("\nConversione unità completata")
