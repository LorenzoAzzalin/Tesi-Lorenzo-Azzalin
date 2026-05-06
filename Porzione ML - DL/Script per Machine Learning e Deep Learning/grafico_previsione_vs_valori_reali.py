import pandas as pd
import matplotlib.pyplot as plt
import os

# Cartella contenente le predizioni generate dal modello finale
percorso_file_predizioni = os.path.join(
    "dataset_intero",
    "previsioni_modello_finale.csv"
)

# Cartella dove salvare i grafici
cartella_output = os.path.join(
    "dataset_intero",
    "grafici_previsioni"
)

os.makedirs(cartella_output, exist_ok=True)


# Variabili target considerate
variabili_target = [
    "u10", "v10", "t2m", "msl",
    "sst", "tcc", "tp_hourly",
    "swh", "pp1d"
]

# Orizzonti temporali
orizzonti = [1, 6, 12, 24]


print("Caricamento file delle predizioni")

# Controllo esistenza file
if not os.path.exists(percorso_file_predizioni):
    raise FileNotFoundError(f"File non trovato: {percorso_file_predizioni}")

df = pd.read_csv(percorso_file_predizioni)

print("Numero totale di righe:", len(df))


# Riduco il numero di punti per rendere i grafici leggibili
dimensione_campione = min(5000, len(df))
df_sample = df.sample(dimensione_campione, random_state=42)

print("Numero di punti utilizzati per i grafici:", len(df_sample))


# Creo i grafici di confronto tra valori reali e predetti
for variabile in variabili_target:

    colonna_reale = f"{variabile}_reale"

    if colonna_reale not in df_sample.columns:
        print(f"Valori reali mancanti per {variabile}")
        continue

    valori_reali = df_sample[colonna_reale]

    for orizzonte in orizzonti:

        colonna_pred = f"{variabile}_pred_T{orizzonte}"

        if colonna_pred not in df_sample.columns:
            print(f"Predizioni mancanti per {colonna_pred}")
            continue

        valori_predetti = df_sample[colonna_pred]

        plt.figure(figsize=(6, 6))

        plt.scatter(valori_reali, valori_predetti, alpha=0.3)

        # Linea ideale (predizione perfetta)
        valore_min = min(valori_reali.min(), valori_predetti.min())
        valore_max = max(valori_reali.max(), valori_predetti.max())

        plt.plot(
            [valore_min, valore_max],
            [valore_min, valore_max],
            linestyle="--"
        )

        plt.xlabel("Valore reale")
        plt.ylabel("Valore predetto")
        plt.title(f"{variabile} - Orizzonte T+{orizzonte}")

        plt.tight_layout()

        percorso_grafico = os.path.join(
            cartella_output,
            f"confronto_reale_predetto_{variabile}_T{orizzonte}.png"
        )

        plt.savefig(percorso_grafico, dpi=300)
        plt.close()

        print("Grafico salvato:", percorso_grafico)


print("\nCreazione grafici completata")
