import xarray as xr
import os
import pandas as pd

cartella_radice = "dataset_intero"

# Dataset prodotti dal feature engineering
cartella_feature = os.path.join(
    cartella_radice,
    "preparazione_dati",
    "feature_engineering"
)

# Cartella dove salvare i dataset finali per il Deep Learning
# (train, validation e test separati)
cartella_output = os.path.join(
    cartella_radice,
    "preparazione_dati",
    "dataset_pronto_dl"
)

# Creazione cartella output se non esiste
os.makedirs(cartella_output, exist_ok=True)


# Percentuali di split temporale
# La somma deve essere pari a 1
rapporto_train = 0.7
rapporto_validazione = 0.15
rapporto_test = 0.15

assert abs(rapporto_train + rapporto_validazione + rapporto_test - 1.0) < 1e-6


# Individuazione automatica delle regioni
regioni = [
    nome for nome in os.listdir(cartella_feature)
    if os.path.isdir(os.path.join(cartella_feature, nome))
]

print("Regioni trovate:", regioni)


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


# Ciclo sulle regioni
for i, regione in enumerate(regioni):

    print("\nElaborazione regione:", regione, f"({i+1}/{len(regioni)})")

    percorso_input = os.path.join(
        cartella_feature,
        regione,
        "dataset_feature_engineered_ciclico.nc"
    )

    if not os.path.isfile(percorso_input):
        print("Dataset non trovato, salto regione")
        continue

    cartella_regione = os.path.join(cartella_output, regione)
    os.makedirs(cartella_regione, exist_ok=True)

    file_train = os.path.join(cartella_regione, "era5_train.nc")
    file_val = os.path.join(cartella_regione, "era5_val.nc")
    file_test = os.path.join(cartella_regione, "era5_test.nc")

    # Se i file esistono già, evita di rifare lo split
    if all(os.path.isfile(f) for f in [file_train, file_val, file_test]):
        print("Split già eseguito, salto")
        continue

    print("Apertura dataset:", percorso_input)

    dataset = xr.open_dataset(percorso_input)

    # Chunking per lavorare con dataset di grandi dimensioni
    dataset = dataset.chunk({
        "valid_time": 500,
        "latitude": 50,
        "longitude": 50
    })

    # Numero totale di timestep
    n = dataset.sizes["valid_time"]

    # Calcolo degli indici di split (senza shuffle)
    idx_train = int(n * rapporto_train)
    idx_val = int(n * (rapporto_train + rapporto_validazione))

    # Non viene effettuato alcuno shuffle
    # Si mantiene l'ordine cronologico e si evita data leakage
    train = dataset.isel(valid_time=slice(0, idx_train))
    val = dataset.isel(valid_time=slice(idx_train, idx_val))
    test = dataset.isel(valid_time=slice(idx_val, n))

    print("Train:", train.sizes["valid_time"])
    print("Validation:", val.sizes["valid_time"])
    print("Test:", test.sizes["valid_time"])

    # Definizione encoding temporale
    for ds in [train, val, test]:
        ds["valid_time"].encoding = {
            "units": "hours since 1970-01-01",
            "dtype": "float64"
        }

    print("Salvataggio dataset")

    # Salvataggio dataset separati
    train.to_netcdf(file_train, encoding=costruisci_encoding(train))
    val.to_netcdf(file_val, encoding=costruisci_encoding(val))
    test.to_netcdf(file_test, encoding=costruisci_encoding(test))

    print("Salvataggio completato")

    # CSV di controllo per verifica manuale
    print("Creazione CSV di controllo")

    train_sample = train.isel(valid_time=0).compute()
    val_sample = val.isel(valid_time=0).compute()
    test_sample = test.isel(valid_time=0).compute()

    train_sample.to_dataframe().reset_index().to_csv(
        os.path.join(cartella_regione, "train_sample.csv"),
        sep=";",
        decimal=".",
        index=False
    )

    val_sample.to_dataframe().reset_index().to_csv(
        os.path.join(cartella_regione, "val_sample.csv"),
        sep=";",
        decimal=".",
        index=False
    )

    test_sample.to_dataframe().reset_index().to_csv(
        os.path.join(cartella_regione, "test_sample.csv"),
        sep=";",
        decimal=".",
        index=False
    )

    dataset.close()
    train.close()
    val.close()
    test.close()


print("\nSplit temporale completato")
print("Output salvati in:", cartella_output)
