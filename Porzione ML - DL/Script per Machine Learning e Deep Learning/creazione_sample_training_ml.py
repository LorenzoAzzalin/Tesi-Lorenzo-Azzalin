import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import pyarrow as pa
import os
import numpy as np

# Cartella contenente il dataset Parquet globale (già unificato)
cartella_dataset = "dataset_intero/preparazione_dati/dataset_pronto_ml"

# File Parquet completo generato nella fase precedente
file_input = os.path.join(
    cartella_dataset,
    "dataset_ml_pronto.parquet"
)

# File di output contenente il campione ridotto
# Questo dataset verrà utilizzato per il training ML (riduzione dimensione)
file_output = os.path.join(
    cartella_dataset,
    "dataset_ml_sample_10M.parquet"
)

# Numero totale di righe da estrarre (target finale)
dimensione_sample = 10_000_000

# Numero di righe lette per ogni blocco (streaming)
# Serve per non caricare tutto il dataset in memoria
dimensione_blocco = 200_000

# Regioni presenti nel dataset
# Utilizzate per garantire copertura geografica nel campione
regioni = [
    "mediterraneo",
    "atlantico",
    "pacifico",
    "indiano"
]

# Percentuale minima di dati da garantire per ogni regione
# Evita squilibri geografici nel dataset finale
frazione_minima_per_regione = 0.05
minimo_per_regione = int(dimensione_sample * frazione_minima_per_regione)

# Probabilità di selezione casuale delle righe
# Determina quanto aggressivo è il campionamento
probabilita_campionamento = 0.05

# Apertura del dataset Parquet in modalità streaming (lazy)
# Non carica tutto in memoria, ma legge a blocchi
dataset = ds.dataset(file_input, format="parquet")

# Writer per scrittura incrementale del dataset finale
# Evita di mantenere tutto il dataset campionato in RAM
writer = None

totale_raccolto = 0

print("Creazione campione ML (10 milioni di righe con copertura regionale)...")

# Si assicura che ogni regione sia rappresentata nel dataset finale
for regione in regioni:

    print("\nFase 1 - Regione:", regione)

    righe_regione = 0

    # Scanner filtrato per regione
    # Legge solo le righe appartenenti alla regione corrente
    scanner = dataset.scanner(
        filter=(ds.field("region") == regione),
        batch_size=dimensione_blocco,
        use_threads=True
    )

    for batch in scanner.to_batches():

        # Se raggiunto il minimo per la regione, si passa alla successiva
        if righe_regione >= minimo_per_regione:
            break

        df = batch.to_pandas()

        if df.empty:
            continue

        # Calcolo righe ancora necessarie
        rimanenti_regione = minimo_per_regione - righe_regione
        rimanenti_globali = dimensione_sample - totale_raccolto

        if rimanenti_globali <= 0:
            break

        # Campionamento casuale del blocco
        maschera = np.random.rand(len(df)) < probabilita_campionamento
        df_campionato = df[maschera]

        if df_campionato.empty:
            continue

        # Limita al minimo richiesto per regione
        if len(df_campionato) > rimanenti_regione:
            df_campionato = df_campionato.sample(n=rimanenti_regione, random_state=42)

        # Limita al totale globale
        if len(df_campionato) > rimanenti_globali:
            df_campionato = df_campionato.sample(n=rimanenti_globali, random_state=42)

        df_campionato = df_campionato.reset_index(drop=True)

        righe_regione += len(df_campionato)
        totale_raccolto += len(df_campionato)

        # Conversione in formato PyArrow
        tabella = pa.Table.from_pandas(df_campionato, preserve_index=False)

        # Inizializzazione writer (una sola volta)
        if writer is None:
            writer = pq.ParquetWriter(
                file_output,
                tabella.schema,
                compression="snappy"
            )

        # Scrittura incrementale
        writer.write_table(tabella)

        print(f"{regione}: {righe_regione}/{minimo_per_regione} | totale: {totale_raccolto}/{dimensione_sample}")

    print(f"Copertura minima raggiunta per {regione}: {righe_regione}")

# Riempie il dataset fino alla dimensione target mantenendo casualità globale
print("\nFase 2 - Riempimento globale del dataset")

for regione in regioni:

    if totale_raccolto >= dimensione_sample:
        break

    print("\nRegione:", regione)

    scanner = dataset.scanner(
        filter=(ds.field("region") == regione),
        batch_size=dimensione_blocco,
        use_threads=True
    )

    for batch in scanner.to_batches():

        if totale_raccolto >= dimensione_sample:
            break

        df = batch.to_pandas()

        if df.empty:
            continue

        rimanenti_globali = dimensione_sample - totale_raccolto

        # Campionamento casuale
        maschera = np.random.rand(len(df)) < probabilita_campionamento
        df_campionato = df[maschera]

        if df_campionato.empty:
            continue

        # Limita al numero totale richiesto
        if len(df_campionato) > rimanenti_globali:
            df_campionato = df_campionato.sample(n=rimanenti_globali, random_state=42)

        df_campionato = df_campionato.reset_index(drop=True)

        totale_raccolto += len(df_campionato)

        tabella = pa.Table.from_pandas(df_campionato, preserve_index=False)
        writer.write_table(tabella)

        print(f"Totale raccolto: {totale_raccolto}/{dimensione_sample}")

# Chiusura del writer (fondamentale per salvare correttamente il file)
if writer is not None:
    writer.close()

print("\nCampione ML completato")
print("File salvato in:", file_output)
