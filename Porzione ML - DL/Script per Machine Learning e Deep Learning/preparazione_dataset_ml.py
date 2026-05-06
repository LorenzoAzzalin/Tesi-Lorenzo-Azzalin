import pandas as pd
import os
import pyarrow as pa
import pyarrow.parquet as pq
import time

# Cartella contenente i file Parquet generati nella fase di flatten (uno o più chunk per regione)
cartella_input = os.path.join(
    "dataset_intero",
    "preparazione_dati",
    "dataset_pronto_ml"
)

# Cartella di output per il dataset finale unificato (stesso path per coerenza pipeline)
cartella_output = os.path.join(
    "dataset_intero",
    "preparazione_dati",
    "dataset_pronto_ml"
)

os.makedirs(cartella_output, exist_ok=True)

# File Parquet finale che conterrà tutti i dati (tutte le regioni)
file_output = os.path.join(
    cartella_output,
    "dataset_ml_pronto.parquet"
)

# Regioni da elaborare (coerenti con la pipeline precedente)
regioni = [
    "atlantico",
    "indiano",
    "mediterraneo",
    "pacifico"
]

# Variabili target che devono essere presenti nel dataset finale
# Servono per il training dei modelli ML multi-target
variabili_target = [
    "u10",
    "v10",
    "t2m",
    "msl",
    "sst",
    "tcc",
    "tp_hourly",
    "swh",
    "pp1d"
]

# Colonne non necessarie (metadati o variabili inutili per il training)
colonne_da_rimuovere = ["number", "expver"]

# Writer Parquet (inizializzato una sola volta per scrittura incrementale)
writer = None

totale_righe = 0
tempo_inizio = time.time()


for regione in regioni:

    print("\nElaborazione regione:", regione)

    # Cartella contenente i chunk Parquet della regione
    cartella_regione = os.path.join(cartella_input, regione)

    if not os.path.isdir(cartella_regione):
        print("Cartella non trovata:", cartella_regione)
        continue

    # Lista dei file Parquet (chunk)
    file_parquet = sorted([
        f for f in os.listdir(cartella_regione)
        if f.endswith(".parquet")
    ])

    for nome_file in file_parquet:

        percorso_file = os.path.join(cartella_regione, nome_file)

        print("Lettura file:", nome_file)

        # Lettura del chunk
        df = pd.read_parquet(percorso_file)

        # Aggiunta della colonna "region" per mantenere informazione geografica
        # Utile per analisi successive o modelli che includono la regione come feature
        df["region"] = regione

        # Rimozione colonne non necessarie
        df = df.drop(columns=colonne_da_rimuovere, errors="ignore")

        # Mantiene solo le righe con almeno un target valido
        # Evita di includere osservazioni completamente prive di informazione utile
        target_presenti = [t for t in variabili_target if t in df.columns]
        if target_presenti:
            maschera_valida = df[target_presenti].notna().any(axis=1)
            df = df[maschera_valida]

        if df.empty:
            print("File vuoto dopo filtraggio, salto")
            continue

        # Uniforma il tipo delle variabili numeriche
        # Evita problemi di mismatch schema tra chunk diversi
        for colonna in df.select_dtypes(include=["float32", "float64"]).columns:
            df[colonna] = df[colonna].astype("float32")

        righe = len(df)
        totale_righe += righe

        print(f"Righe valide: {righe} - Totale finora: {totale_righe}")

        # Conversione da pandas a formato PyArrow
        tabella = pa.Table.from_pandas(df)

        # Inizializzazione del writer Parquet (una sola volta)
        # Garantisce uno schema coerente per tutto il dataset
        if writer is None:
            writer = pq.ParquetWriter(
                file_output,
                tabella.schema,
                compression="snappy"
            )

        # Scrittura incrementale del chunk
        writer.write_table(tabella)


# Chiusura del writer (fondamentale per finalizzare il file)
if writer is not None:
    writer.close()

tempo_totale = time.time() - tempo_inizio

print("\nDataset ML pronto")
print("File salvato in:", file_output)
print("Numero totale di righe:", totale_righe)
print(f"Tempo totale: {tempo_totale/60:.2f} minuti")
