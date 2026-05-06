import os
import xarray as xr
import pandas as pd
import time


cartella_radice = "dataset_intero"
cartella_preprocessing = os.path.join(cartella_radice, "preparazione_dati", "preprocessing")


def forza_datetime_per_csv(dataset, nome_tempo="valid_time"):
    if nome_tempo in dataset.coords:
        dataset = dataset.copy()
        dataset[nome_tempo] = dataset[nome_tempo].dt.strftime("%Y-%m-%d %H:%M:%S")
    return dataset


variabili_fondamentali = ["swh", "pp1d", "u10", "v10"]
variabili_interpolabili = ["t2m", "sst", "msl", "tcc", "tp_hourly"]


regioni = [
    nome for nome in os.listdir(cartella_preprocessing)
    if os.path.isdir(os.path.join(cartella_preprocessing, nome))
]

print("Regioni trovate:", regioni)

tempo_inizio_pipeline = time.time()


for indice, regione in enumerate(regioni):

    tempo_inizio_regione = time.time()
    print("\nElaborazione regione:", regione)

    cartella_regione = os.path.join(cartella_preprocessing, regione)
    cartella_output = os.path.join(cartella_regione, "dataset_pulito")

    if os.path.isdir(cartella_output):
        print("Cartella dataset_pulito già presente, salto regione")
        continue

    percorso_input = os.path.join(cartella_regione, "dataset_regionale_unita.nc")

    if not os.path.isfile(percorso_input):
        print("Dataset di input non trovato, salto regione")
        continue

    os.makedirs(cartella_output, exist_ok=True)

    percorso_output_nc = os.path.join(cartella_output, "dataset_regionale_pulito.nc")
    percorso_output_csv = os.path.join(cartella_output, "dataset_regionale_pulito_sample.csv")

    print("Apertura dataset")

    dataset = xr.open_dataset(
        percorso_input,
        chunks={
            "valid_time": 500,
            "latitude": 50,
            "longitude": 50
        }
    )

    print("Calcolo percentuale NaN combinata su variabili fondamentali")

    percentuali_nan = []

    for variabile in variabili_fondamentali:
        if variabile in dataset:
            percentuali_nan.append(
                dataset[variabile].isnull().mean(dim="valid_time")
            )

    if len(percentuali_nan) == 0:
        print("Nessuna variabile fondamentale trovata, salto regione")
        dataset.close()
        continue

    percentuale_nan = sum(percentuali_nan) / len(percentuali_nan)

    soglia_nan = 0.5

    print("Creazione maschera mare valido")

    maschera_valida = (percentuale_nan <= soglia_nan).compute()

    print("Riduzione dominio spaziale con soglia percentuale")

    percentuale_lat = maschera_valida.mean(dim="longitude")
    percentuale_lon = maschera_valida.mean(dim="latitude")

    soglia_spaziale = 0.3

    lat_valide = (percentuale_lat > soglia_spaziale).compute()
    lon_valide = (percentuale_lon > soglia_spaziale).compute()

    dataset = dataset.sel(
        latitude=dataset.latitude[lat_valide],
        longitude=dataset.longitude[lon_valide]
    )

    print("Interpolazione dei valori mancanti (solo variabili continue)")

    for variabile in variabili_interpolabili:
        if variabile in dataset.data_vars:

            print("Interpolazione variabile:", variabile)

            dati = dataset[variabile]

            dati = dati.chunk({"valid_time": -1})

            dati = dati.interpolate_na(
                dim="valid_time",
                method="linear",
                limit=2
            )

            dataset[variabile] = dati

    print("Filtro timestep non validi")

    maschera_valida_tempo = None

    for variabile in variabili_fondamentali:
        if variabile in dataset.data_vars:

            validita = dataset[variabile].notnull().any(dim=["latitude", "longitude"])

            if maschera_valida_tempo is None:
                maschera_valida_tempo = validita
            else:
                maschera_valida_tempo = maschera_valida_tempo & validita

    if maschera_valida_tempo is None:
        print("Nessuna variabile fondamentale trovata, salto regione")
        dataset.close()
        continue

    dataset_pulito = dataset.sel(valid_time=maschera_valida_tempo)

    print("Numero timestep originali:", dataset.sizes.get("valid_time", 0))
    print("Numero timestep dopo pulizia:", dataset_pulito.sizes.get("valid_time", 0))

    print("Conversione dati in float32")

    dataset_pulito = dataset_pulito.astype("float32")

    print("Definizione chunk dinamici")

    dim_time = dataset_pulito.sizes["valid_time"]
    dim_lat = dataset_pulito.sizes["latitude"]
    dim_lon = dataset_pulito.sizes["longitude"]

    chunk_time = min(72, dim_time)
    chunk_lat = min(50, dim_lat)
    chunk_lon = min(50, dim_lon)

    dataset_pulito = dataset_pulito.chunk({
        "valid_time": chunk_time,
        "latitude": chunk_lat,
        "longitude": chunk_lon
    })

    print("Reset encoding")

    for variabile in list(dataset_pulito.data_vars) + list(dataset_pulito.coords):
        dataset_pulito[variabile].encoding = {}

    print("Salvataggio dataset compresso")

    encoding = {
        var: {
            "zlib": True,
            "complevel": 3,
            "chunksizes": (chunk_time, chunk_lat, chunk_lon)
        }
        for var in dataset_pulito.data_vars
    }

    dataset_pulito.to_netcdf(
        percorso_output_nc,
        engine="netcdf4",
        encoding=encoding
    )

    print("Dataset salvato in:", percorso_output_nc)

    print("Creazione CSV di controllo")

    dataset_sample = dataset_pulito.isel(valid_time=0).compute()
    dataset_csv = forza_datetime_per_csv(dataset_sample)

    dataframe = dataset_csv.to_dataframe().reset_index()

    dataframe.to_csv(
        percorso_output_csv,
        sep=";",
        decimal=".",
        index=False
    )

    print("CSV salvato in:", percorso_output_csv)

    dataset.close()
    dataset_pulito.close()

    tempo_regione = time.time() - tempo_inizio_regione
    regioni_rimanenti = len(regioni) - (indice + 1)
    tempo_restante = tempo_regione * regioni_rimanenti

    print("Tempo elaborazione regione (min):", round(tempo_regione / 60, 2))
    print("Tempo stimato rimanente (min):", round(tempo_restante / 60, 2))


tempo_totale = time.time() - tempo_inizio_pipeline
print("\nTempo totale pipeline (min):", round(tempo_totale / 60, 2))
