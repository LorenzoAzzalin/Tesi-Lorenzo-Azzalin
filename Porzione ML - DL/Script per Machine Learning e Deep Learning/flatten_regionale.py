import xarray as xr
import pandas as pd
import os
import numpy as np

# Cartella input (output del feature engineering)
# Contiene dataset NetCDF con struttura spazio-temporale
cartella_input = "dataset_intero/preparazione_dati/feature_engineering"

# Cartella output finale per i modelli di Machine Learning
# Qui i dati vengono salvati in formato tabellare (Parquet)
cartella_output = os.path.join(
    "dataset_intero",
    "preparazione_dati",
    "dataset_pronto_ml"
)

os.makedirs(cartella_output, exist_ok=True)

# Regioni considerate (coerenti con la pipeline)
regioni = [
    "atlantico",
    "indiano",
    "mediterraneo",
    "pacifico"
]

# Dimensione del chunk temporale
# Serve per evitare di caricare tutto il dataset in memoria
dimensione_chunk_temporale = 24

# Frazione di campionamento delle osservazioni normali
# Riduce drasticamente il numero di righe mantenendo rappresentatività
frazione_campionamento = 0.02

# Soglia per identificare eventi estremi (onde alte)
# Serve per dare più peso a condizioni rare ma importanti
soglia_altezza_onda = 3.0


for regione in regioni:

    print("\nAvvio flatten (Parquet) per la regione:", regione)

    # Percorso dataset NetCDF con feature engineering completato
    file_input = os.path.join(
        cartella_input,
        regione,
        "dataset_feature_engineered_ciclico.nc"
    )

    # Cartella di output specifica per regione
    cartella_output_regione = os.path.join(cartella_output, regione)
    os.makedirs(cartella_output_regione, exist_ok=True)

    print("Apertura dataset NetCDF")

    # Apertura dataset (formato multidimensionale)
    dataset = xr.open_dataset(file_input)

    numero_timestep = dataset.sizes["valid_time"]
    print("Numero totale di timestep:", numero_timestep)

    totale_righe = 0
    indice_chunk = 0

    # Loop temporale a blocchi per evitare overload memoria
    for inizio in range(0, numero_timestep, dimensione_chunk_temporale):

        fine = min(inizio + dimensione_chunk_temporale, numero_timestep)

        print(f"Elaborazione timestep {inizio} → {fine}")

        # Selezione sottoinsieme temporale
        sotto_dataset = dataset.isel(valid_time=slice(inizio, fine))

        # Conversione da formato griglia (xarray) a formato tabellare (pandas)
        df = sotto_dataset.to_dataframe().reset_index()

        # Rimozione delle righe prive di variabili fondamentali
        # Garantisce che il modello abbia informazione minima significativa
        df = df.dropna(subset=["swh", "pp1d", "u10", "v10"])

        if len(df) == 0:
            continue

        # Separazione tra:
        # - eventi estremi (onde alte)
        # - condizioni normali
        df_estremi = df[df["swh"] > soglia_altezza_onda]
        df_normali = df[df["swh"] <= soglia_altezza_onda]

        # Campionamento casuale delle condizioni normali
        # Riduce la dimensione del dataset mantenendo varietà
        df_normali_campionato = df_normali.sample(
            frac=frazione_campionamento,
            random_state=42
        )

        # Campionamento meno aggressivo per eventi estremi
        # Serve a evitare che eventi rari vengano sottorappresentati
        df_estremi_campionato = df_estremi.sample(
            frac=min(1.0, frazione_campionamento * 5),
            random_state=42
        )

        # Unione dei due insiemi
        # Risultato: dataset bilanciato tra normale ed estremo
        df_finale = pd.concat([df_normali_campionato, df_estremi_campionato])

        totale_righe += len(df_finale)

        # Salvataggio in formato Parquet (ottimizzato per ML)
        # Ogni chunk viene salvato separatamente per scalabilità
        file_chunk = os.path.join(
            cartella_output_regione,
            f"chunk_{indice_chunk:04d}.parquet"
        )

        df_finale.to_parquet(file_chunk, index=False)

        indice_chunk += 1

        print("Righe salvate finora:", totale_righe)

    dataset.close()

    print("Regione completata:", regione)
    print("Totale righe:", totale_righe)

print("\nFlatten completato: dataset salvati in dataset_pronto_ml")
