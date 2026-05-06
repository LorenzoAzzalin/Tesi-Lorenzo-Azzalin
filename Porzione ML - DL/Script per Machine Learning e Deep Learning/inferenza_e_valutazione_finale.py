import os
import pandas as pd
import joblib
import json
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error

# Dataset tabellare per orizzonte T+1 usato per generare le predizioni
percorso_dataset = os.path.join(
    "dataset_intero",
    "preparazione_dati",
    "dataset_pronto_ml",
    "dataset_ml_T1.parquet"
)

# Cartella contenente i modelli finali salvati per ciascun orizzonte
cartella_modelli = os.path.join(
    "dataset_intero",
    "modello_finale"
)

# File JSON con il miglior modello ML selezionato in fase di valutazione
percorso_miglior_modello = os.path.join(
    "dataset_intero",
    "confronto_modelli",
    "valutazione_modelli",
    "miglior_modello_ml.json"
)

# File di output con tutte le predizioni
percorso_output = os.path.join(
    "dataset_intero",
    "previsioni_modello_finale.csv"
)

# Cartella per salvare i grafici di confronto reale vs predetto
cartella_grafici = os.path.join(
    "dataset_intero",
    "grafici_previsioni"
)

os.makedirs(cartella_grafici, exist_ok=True)

# Variabili target previste
variabili_target = [
    "u10", "v10", "t2m", "msl",
    "sst", "tcc", "tp_hourly",
    "swh", "pp1d"
]

# Orizzonti temporali considerati
orizzonti = [1, 6, 12, 24]


# Caricamento dataset
df = pd.read_parquet(percorso_dataset)

# Definizione feature (tutte le colonne tranne target e metadati)
colonne_feature = [
    c for c in df.columns
    if c not in variabili_target
    and c not in ["region", "number", "expver"]
]

X = df[colonne_feature]

# Caricamento informazioni sul miglior modello ML
with open(percorso_miglior_modello) as f:
    info_modello = json.load(f)

nome_modello = info_modello["modello"]

# DataFrame che conterrà tutte le predizioni
df_pred = pd.DataFrame(index=df.index)

# Loop sugli orizzonti e sulle variabili target
for orizzonte in orizzonti:

    cartella_T = os.path.join(cartella_modelli, f"T{orizzonte}")

    for var in variabili_target:

        path = os.path.join(cartella_T, f"{nome_modello}_{var}.pkl")

        # Se il modello non esiste per quella combinazione, si salta
        if not os.path.exists(path):
            continue

        modello = joblib.load(path)

        # Predizione per tutte le osservazioni
        df_pred[f"{var}_pred_T{orizzonte}"] = modello.predict(X)


# Aggiunta dei valori reali per confronto
for var in variabili_target:
    df_pred[f"{var}_reale"] = df[var]

# Salvataggio completo delle predizioni
df_pred.to_csv(percorso_output, index=False)

print("Predizioni salvate")


# Creazione grafici e calcolo metriche su un sottoinsieme
df_sample = df_pred.sample(min(5000, len(df_pred)), random_state=42)

for var in variabili_target:
    for orizzonte in orizzonti:

        pred_col = f"{var}_pred_T{orizzonte}"
        real_col = f"{var}_reale"

        if pred_col not in df_sample:
            continue

        x = df_sample[real_col]
        y = df_sample[pred_col]

        # Scatter plot reale vs predetto
        plt.figure(figsize=(6,6))
        plt.scatter(x, y, alpha=0.3)

        # Linea ideale y = x
        min_val = min(x.min(), y.min())
        max_val = max(x.max(), y.max())

        plt.plot([min_val, max_val], [min_val, max_val], linestyle="--")

        plt.title(f"{var} T+{orizzonte}")
        plt.xlabel("Reale")
        plt.ylabel("Predetto")

        plt.savefig(os.path.join(cartella_grafici, f"{var}_T{orizzonte}.png"))
        plt.close()

        # Calcolo RMSE sul campione
        rmse = np.sqrt(mean_squared_error(x, y))
        print(f"{var} T+{orizzonte} RMSE: {rmse:.3f}")
