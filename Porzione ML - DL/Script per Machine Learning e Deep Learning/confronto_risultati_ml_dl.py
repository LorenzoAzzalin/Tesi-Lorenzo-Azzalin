import pandas as pd
import matplotlib.pyplot as plt
import os

# Cartella contenente i risultati dei modelli di machine learning
# Qui sono salvati i file csv generati durante il training ML
cartella_risultati_ml = os.path.join(
    "dataset_intero",
    "machine_learning",
    "risultati"
)

# Cartella contenente i risultati del modello deep learning (ConvLSTM)
# Contiene il file risultati_convlstm.csv prodotto dallo script di valutazione
cartella_risultati_dl = os.path.join(
    "dataset_intero",
    "deep_learning",
    "risultati"
)

# Cartella dove verranno salvati dataset di confronto e grafici
cartella_confronto = os.path.join(
    "dataset_intero",
    "confronto_modelli"
)

os.makedirs(cartella_confronto, exist_ok=True)


# Percorsi dei file ML per ciascun orizzonte temporale
percorsi_file_ml = {
    1: os.path.join(cartella_risultati_ml, "ml_risultati_T1.csv"),
    6: os.path.join(cartella_risultati_ml, "ml_risultati_T6.csv"),
    12: os.path.join(cartella_risultati_ml, "ml_risultati_T12.csv"),
    24: os.path.join(cartella_risultati_ml, "ml_risultati_T24.csv"),
}

# Percorso del file dei risultati deep learning
percorso_file_dl = os.path.join(
    cartella_risultati_dl,
    "risultati_convlstm.csv"
)

# Percorsi dei file di output
percorso_output_confronto = os.path.join(
    cartella_confronto,
    "confronto_ml_deep_learning.csv"
)

percorso_grafico_rmse = os.path.join(
    cartella_confronto,
    "grafico_confronto_rmse_T1.png"
)

percorso_grafico_orizzonte = os.path.join(
    cartella_confronto,
    "grafico_rmse_vs_orizzonte.png"
)


# Caricamento risultati machine learning
lista_risultati_ml = []

print("Caricamento risultati machine learning")

for orizzonte, percorso_file in percorsi_file_ml.items():

    if not os.path.exists(percorso_file):
        print(f"File non trovato, salto: {percorso_file}")
        continue

    df = pd.read_csv(percorso_file)

    # Uniforma i nomi delle colonne per evitare inconsistenze tra file
    df.columns = [colonna.lower().strip() for colonna in df.columns]

    # Aggiunta informazioni utili per il confronto
    df["orizzonte"] = orizzonte
    df["tipo_modello"] = "machine_learning"
    df["modello"] = df["modello"].str.lower()

    lista_risultati_ml.append(df)

if not lista_risultati_ml:
    raise ValueError("Nessun file di risultati ML trovato")

df_ml = pd.concat(lista_risultati_ml, ignore_index=True)


print("Caricamento risultati deep learning")

if not os.path.exists(percorso_file_dl):
    raise FileNotFoundError(f"File DL mancante: {percorso_file_dl}")

df_dl = pd.read_csv(percorso_file_dl)

# Uniforma i nomi delle colonne
df_dl.columns = [colonna.lower().strip() for colonna in df_dl.columns]

# Aggiunta metadati
df_dl["modello"] = "convlstm"
df_dl["tipo_modello"] = "deep_learning"

# Il ConvLSTM è stato valutato solo su T+1
df_dl["orizzonte"] = 1


# Unione risultati ML e DL
df_confronto = pd.concat([df_ml, df_dl], ignore_index=True)

# Salvataggio dataset di confronto
df_confronto.to_csv(percorso_output_confronto, index=False)

print("\nDataset di confronto salvato in:")
print(percorso_output_confronto)


# Calcolo metriche medie per combinazione di target, modello e orizzonte
df_riassunto = (
    df_confronto
    .groupby(["target", "modello", "tipo_modello", "orizzonte"])[["rmse", "mae", "r2"]]
    .mean()
    .reset_index()
)

print("\nPrime righe del riepilogo:")
print(df_riassunto.head())


# Grafico RMSE per ciascuna variabile nel caso T+1
df_pivot = (
    df_riassunto[df_riassunto["orizzonte"] == 1]
    .groupby(["target", "modello"])["rmse"]
    .mean()
    .unstack()
)

df_pivot.plot(kind="bar", figsize=(12, 6))

plt.title("Confronto RMSE per ciascuna variabile (T+1)")
plt.xlabel("Variabile target")
plt.ylabel("RMSE")

plt.xticks(rotation=45)
plt.grid(axis="y", linestyle="--", alpha=0.6)

plt.tight_layout()
plt.savefig(percorso_grafico_rmse, dpi=300)
plt.close()

print("Grafico RMSE salvato in:", percorso_grafico_rmse)


# Grafico andamento RMSE al crescere dell’orizzonte (solo ML)
df_andamento = (
    df_riassunto[df_riassunto["tipo_modello"] == "machine_learning"]
    .groupby(["orizzonte"])["rmse"]
    .mean()
    .reset_index()
)

plt.figure(figsize=(8, 5))
plt.plot(df_andamento["orizzonte"], df_andamento["rmse"], marker="o")

plt.title("Variazione RMSE al crescere dell'orizzonte temporale")
plt.xlabel("Orizzonte (ore)")
plt.ylabel("RMSE")

plt.grid(True)

plt.tight_layout()
plt.savefig(percorso_grafico_orizzonte, dpi=300)
plt.close()

print("Grafico RMSE vs orizzonte salvato in:", percorso_grafico_orizzonte)


print("\nConfronto tra modelli completato")
