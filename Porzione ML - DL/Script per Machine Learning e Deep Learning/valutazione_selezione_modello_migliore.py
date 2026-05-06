import pandas as pd
import matplotlib.pyplot as plt
import os
import json

# Cartella contenente il dataset di confronto tra ML e deep learning
cartella_confronto = os.path.join("dataset_intero", "confronto_modelli")

# File di input prodotto dallo script di confronto modelli
percorso_file_confronto = os.path.join(
    cartella_confronto,
    "confronto_ml_deep_learning.csv"
)

# Cartella di output per riepiloghi e selezione dei modelli migliori
cartella_output = os.path.join(
    cartella_confronto,
    "valutazione_modelli"
)

os.makedirs(cartella_output, exist_ok=True)

# File di riepilogo aggregato
percorso_riepilogo = os.path.join(
    cartella_output,
    "riepilogo_modelli_T1.csv"
)

# File JSON con il miglior modello ML
percorso_miglior_ml = os.path.join(
    cartella_output,
    "miglior_modello_ml.json"
)

# File JSON con il miglior modello DL
percorso_miglior_dl = os.path.join(
    cartella_output,
    "miglior_modello_dl.json"
)


print("Caricamento dataset confronto")

# Caricamento dataset completo
df = pd.read_csv(percorso_file_confronto)

# Rimozione righe con metriche mancanti
df = df.dropna(subset=["rmse", "mae", "r2"])

# Selezione solo orizzonte T+1 (unico caso confrontabile tra ML e DL)
df_t1 = df[df["orizzonte"] == 1]

# Calcolo metriche medie per modello
# Il confronto viene fatto aggregando su tutte le variabili target
df_riepilogo = (
    df_t1
    .groupby(["modello", "tipo_modello"])[["rmse", "mae", "r2"]]
    .mean()
    .reset_index()
    .sort_values("rmse")
)

# Salvataggio del riepilogo ordinato per RMSE
df_riepilogo.to_csv(percorso_riepilogo, index=False)

print("\nRiepilogo:")
print(df_riepilogo)


# Separazione tra modelli machine learning e deep learning
df_ml = df_riepilogo[df_riepilogo["tipo_modello"] == "machine_learning"]
df_dl = df_riepilogo[df_riepilogo["tipo_modello"] == "deep_learning"]

# Selezione del miglior modello (minimo RMSE)
miglior_ml = df_ml.iloc[0]
miglior_dl = df_dl.iloc[0]


# Creazione dizionario con informazioni modello ML
info_ml = {
    "modello": miglior_ml["modello"],
    "tipo_modello": "machine_learning",
    "rmse": float(miglior_ml["rmse"]),
    "mae": float(miglior_ml["mae"]),
    "r2": float(miglior_ml["r2"]),
    "orizzonte": 1
}

# Creazione dizionario con informazioni modello DL
info_dl = {
    "modello": miglior_dl["modello"],
    "tipo_modello": "deep_learning",
    "rmse": float(miglior_dl["rmse"]),
    "mae": float(miglior_dl["mae"]),
    "r2": float(miglior_dl["r2"]),
    "orizzonte": 1
}


# Salvataggio risultati in formato JSON
with open(percorso_miglior_ml, "w") as f:
    json.dump(info_ml, f, indent=4)

with open(percorso_miglior_dl, "w") as f:
    json.dump(info_dl, f, indent=4)


print("\nMiglior ML:", info_ml)
print("Miglior DL:", info_dl)

print("\nValutazione completata")
