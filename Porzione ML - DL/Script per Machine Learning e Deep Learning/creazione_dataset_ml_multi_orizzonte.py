import pyarrow.dataset as ds
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd
import numpy as np
import os

# Cartella contenente il dataset ML di partenza (già campionato)
cartella_dataset = "dataset_intero/preparazione_dati/dataset_pronto_ml"

# File di input (dataset tabellare ridotto a ~10M righe)
file_input = os.path.join(
    cartella_dataset,
    "dataset_ml_sample_10M.parquet"
)

# File di output per ciascun orizzonte temporale
# Ogni file conterrà un dataset specifico per previsione a T+N
file_output = {
    1: os.path.join(cartella_dataset, "dataset_ml_T1.parquet"),
    6: os.path.join(cartella_dataset, "dataset_ml_T6.parquet"),
    12: os.path.join(cartella_dataset, "dataset_ml_T12.parquet"),
    24: os.path.join(cartella_dataset, "dataset_ml_T24.parquet"),
}

# Numero di righe per ogni blocco letto (streaming)
# Permette di lavorare su dataset grandi senza saturare la memoria
dimensione_blocco = 200_000

# Variabili target da prevedere
# Queste variabili verranno spostate temporalmente (shift) per creare i target futuri
variabili_target = [
    "u10", "v10", "t2m", "msl",
    "sst", "tcc", "tp_hourly",
    "swh", "pp1d"
]

print("Caricamento dataset in modalità streaming")

# Apertura dataset Parquet in modalità lazy (streaming)
# I dati vengono letti a blocchi senza essere caricati completamente in RAM
dataset = ds.dataset(file_input, format="parquet")

# Dizionario che contiene i writer per ogni orizzonte temporale
# Ogni writer consente la scrittura incrementale del dataset corrispondente
scrittori = {}

# Lettura del dataset a blocchi
for blocco in dataset.to_batches(batch_size=dimensione_blocco):

    dataframe = blocco.to_pandas()

    # Ordinamento temporale
    # Fondamentale per garantire che lo shift produca target corretti
    if "valid_time" in dataframe.columns:
        dataframe = dataframe.sort_values("valid_time")

    # Creazione dei dataset per ciascun orizzonte temporale
    for orizzonte in [1, 6, 12, 24]:

        df_orizzonte = dataframe.copy()

        # Shift negativo:
        # associa a ogni riga il valore della variabile target nel futuro (t + orizzonte)
        for variabile in variabili_target:
            df_orizzonte[variabile] = df_orizzonte[variabile].shift(-orizzonte)

        # Rimozione delle righe finali prive di target (non esiste t+N)
        df_orizzonte = df_orizzonte.dropna(subset=variabili_target)

        if df_orizzonte.empty:
            continue

        # Conversione in formato PyArrow per scrittura efficiente
        tabella = pa.Table.from_pandas(df_orizzonte, preserve_index=False)

        # Inizializzazione del writer al primo blocco per ogni orizzonte
        # Garantisce schema coerente per tutto il file
        if orizzonte not in scrittori:
            scrittori[orizzonte] = pq.ParquetWriter(
                file_output[orizzonte],
                tabella.schema,
                compression="snappy"
            )

        # Scrittura incrementale del blocco
        scrittori[orizzonte].write_table(tabella)

        print(f"Orizzonte T+{orizzonte}: blocco processato")

# Chiusura dei file Parquet (necessaria per finalizzare i file)
for writer in scrittori.values():
    writer.close()

print("\nDataset multi-horizon creati:")
for orizzonte, percorso in file_output.items():
    print(f"T+{orizzonte}: {percorso}")
