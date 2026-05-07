import pandas as pd
import matplotlib.pyplot as plt
import os

# Cartella contenente i risultati dei modelli di machine learning
cartella_risultati_ml = os.path.join(
    "dataset_intero",
    "machine_learning",
    "risultati"
)

# Cartella confronto output
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

# Percorso file ConvLSTM

percorso_file_dl_standard = os.path.join(
    "dataset_intero",
    "deep_learning",
    "risultati",
    "risultati_convlstm.csv"
)

percorso_file_dl_locale = "risultati_convlstm.csv"

if os.path.exists(percorso_file_dl_standard):
    percorso_file_dl = percorso_file_dl_standard

elif os.path.exists(percorso_file_dl_locale):
    percorso_file_dl = percorso_file_dl_locale

else:
    raise FileNotFoundError(
        "File risultati_convlstm.csv non trovato"
    )


# Percorsi file output
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

percorso_grafico_globale = os.path.join(
    cartella_confronto,
    "grafico_confronto_globale_modelli.png"
)


# Caricamento risultati ML

lista_risultati_ml = []

print("Caricamento risultati machine learning")

for orizzonte, percorso_file in percorsi_file_ml.items():

    if not os.path.exists(percorso_file):
        print(f"File non trovato, salto: {percorso_file}")
        continue

    df = pd.read_csv(percorso_file)

    # Uniforma nomi colonne
    df.columns = [colonna.lower().strip() for colonna in df.columns]

    # Aggiunta metadati
    df["orizzonte"] = orizzonte
    df["tipo_modello"] = "machine_learning"
    df["modello"] = df["modello"].str.lower()

    lista_risultati_ml.append(df)

if not lista_risultati_ml:
    raise ValueError("Nessun file ML trovato")

df_ml = pd.concat(lista_risultati_ml, ignore_index=True)


# Caricamento risultati ConvLSTM

print("Caricamento risultati ConvLSTM")

df_dl = pd.read_csv(percorso_file_dl)

# Uniforma nomi colonne
df_dl.columns = [colonna.lower().strip() for colonna in df_dl.columns]

print("\nColonne trovate nel CSV ConvLSTM:")
print(df_dl.columns.tolist())


# Rinominazione automatica colonne principali

mappa_colonne = {}

for colonna in df_dl.columns:

    nome = colonna.lower()

    if "rmse" in nome:
        mappa_colonne[colonna] = "rmse"

    elif "mae" in nome:
        mappa_colonne[colonna] = "mae"

    elif nome == "r2" or "r2" in nome:
        mappa_colonne[colonna] = "r2"

    elif "target" in nome or "variabile" in nome:
        mappa_colonne[colonna] = "target"

df_dl = df_dl.rename(columns=mappa_colonne)


# Se il CSV ConvLSTM non contiene target,
# viene creato un target generico

if "target" not in df_dl.columns:
    df_dl["target"] = "convlstm"


# Aggiunta metadati

df_dl["modello"] = "convlstm"
df_dl["tipo_modello"] = "deep_learning"

# ConvLSTM disponibile solo per T+1
df_dl["orizzonte"] = 1


# Unione dataset

df_confronto = pd.concat([df_ml, df_dl], ignore_index=True)

# Salvataggio dataset confronto
df_confronto.to_csv(percorso_output_confronto, index=False)

print("\nDataset confronto salvato:")
print(percorso_output_confronto)


# Riepilogo metriche

df_riassunto = (
    df_confronto
    .groupby(
        ["target", "modello", "tipo_modello", "orizzonte"]
    )[["rmse", "mae", "r2"]]
    .mean()
    .reset_index()
)

print("\nPrime righe riepilogo:")
print(df_riassunto.head())


# Grafico globale ConvLSTM vs ML

df_globale = (
    df_riassunto[df_riassunto["orizzonte"] == 1]
    .groupby("modello")["rmse"]
    .mean()
    .reset_index()
)

plt.figure(figsize=(8, 5))

plt.bar(
    df_globale["modello"],
    df_globale["rmse"]
)

plt.title("Confronto RMSE medio tra modelli")
plt.xlabel("Modello")
plt.ylabel("RMSE medio")

plt.grid(axis="y", linestyle="--", alpha=0.6)

plt.tight_layout()
plt.savefig(percorso_grafico_globale, dpi=300)
plt.close()

print("\nGrafico confronto globale salvato:")
print(percorso_grafico_globale)


# Grafico RMSE per variabile T+1

df_pivot = (
    df_riassunto[
        (df_riassunto["orizzonte"] == 1) &
        (df_riassunto["tipo_modello"] == "machine_learning")
    ]
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

print("\nGrafico RMSE variabili salvato:")
print(percorso_grafico_rmse)


# Grafico RMSE vs orizzonte

df_andamento = (
    df_riassunto[
        df_riassunto["tipo_modello"] == "machine_learning"
    ]
    .groupby("orizzonte")["rmse"]
    .mean()
    .reset_index()
)

plt.figure(figsize=(8, 5))

plt.plot(
    df_andamento["orizzonte"],
    df_andamento["rmse"],
    marker="o"
)

plt.title("Variazione RMSE al crescere dell'orizzonte temporale")
plt.xlabel("Orizzonte (ore)")
plt.ylabel("RMSE")

plt.grid(True)

plt.tight_layout()
plt.savefig(percorso_grafico_orizzonte, dpi=300)
plt.close()

print("\nGrafico RMSE vs orizzonte salvato:")
print(percorso_grafico_orizzonte)

print("\nConfronto tra modelli completato")
