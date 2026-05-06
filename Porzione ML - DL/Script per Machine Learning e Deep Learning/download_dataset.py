import cdsapi
import os

# Nome del dataset ERA5 utilizzato (single levels).
# Questo dataset contiene variabili atmosferiche e marine su griglia globale.
nome_dataset = "reanalysis-era5-single-levels"

# Lista delle variabili richieste.
# Include:
# - variabili atmosferiche (vento, temperatura, pressione, nuvolosità)
# - variabili marine (SST, onde)
variabili = [
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_temperature",
    "mean_sea_level_pressure",
    "sea_surface_temperature",
    "total_precipitation",
    "total_cloud_cover",
    "significant_height_of_combined_wind_waves_and_swell",
    "mean_wave_direction",
    "peak_wave_period",
]

# Intervallo temporale considerato.
# I dati vengono scaricati su base mensile per migliorare la robustezza del download
# ed evitare richieste troppo pesanti all'API.
anni = [str(a) for a in range(2019, 2025)]
mesi = [f"{m:02d}" for m in range(1, 13)]
giorni = [f"{d:02d}" for d in range(1, 32)]
ore = [f"{h:02d}:00" for h in range(24)]

# Percorsi di base coerenti con la struttura del progetto.
# I dati grezzi vengono salvati separatamente dalle fasi successive della pipeline.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

cartella_dataset = os.path.join(SCRIPT_DIR, "dataset_intero")
cartella_preparazione = os.path.join(cartella_dataset, "preparazione_dati")
cartella_grezzi = os.path.join(cartella_preparazione, "dati_grezzi")

# Definizione delle aree geografiche.
# Le coordinate sono espresse come:
# lat_min, lat_max, lon_min, lon_max
# Ogni regione viene trattata separatamente per:
# - ridurre la dimensione dei dataset
# - migliorare la scalabilità della pipeline
aree = {

    "mediterraneo": dict(
        lat_min=32.0,
        lat_max=46.0,
        lon_min=-6.0,
        lon_max=34.0
    ),

    "atlantico": dict(
        lat_min=-45.0,
        lat_max=60.0,
        lon_min=-75.0,
        lon_max=15.0
    ),

    "pacifico": dict(
        lat_min=-45.0,
        lat_max=50.0,
        lon_min=140.0,
        lon_max=-110.0
    ),

    "indiano": dict(
        lat_min=-30.0,
        lat_max=25.0,
        lon_min=40.0,
        lon_max=110.0
    ),
}

# Inizializzazione del client CDS API.
# Permette di effettuare richieste programmatiche al Copernicus Climate Data Store.
client = cdsapi.Client()

# Creazione cartella dati grezzi (se non esiste).
os.makedirs(cartella_grezzi, exist_ok=True)

# Loop principale di download.
# I dati vengono scaricati separatamente per:
# - regione geografica
# - anno
# - mese
for regione, area in aree.items():

    print("\nRegione:", regione)

    cartella_regione = os.path.join(cartella_grezzi, regione)
    os.makedirs(cartella_regione, exist_ok=True)

    for anno in anni:
        for mese in mesi:

            # Nome del file di output (un file per mese).
            file_output = os.path.join(
                cartella_regione,
                f"era5_single_levels_{anno}_{mese}.nc"
            )

            # Se il file è già presente, il download viene saltato.
            # Questo consente di riprendere il processo in caso di interruzioni.
            if os.path.exists(file_output):
                print("File già presente, salto:", file_output)
                continue

            print("Download:", anno, mese)
            print("Output:", file_output)

            # Richiesta dati all'API ERA5.
            # Parametri principali:
            # - area: bounding box geografica
            # - grid: risoluzione spaziale (0.5° x 0.5°)
            # - time: risoluzione temporale oraria
            client.retrieve(
                nome_dataset,
                {
                    "product_type": "reanalysis",
                    "variable": variabili,
                    "year": anno,
                    "month": mese,
                    "day": giorni,
                    "time": ore,
                    "area": [
                        area["lat_max"],
                        area["lon_min"],
                        area["lat_min"],
                        area["lon_max"],
                    ],
                    "grid": [0.5, 0.5],
                    "format": "netcdf",
                },
                file_output
            )

            print("Download completato:", anno, mese)

print("\nDownload completato per tutte le regioni")
