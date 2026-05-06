import pandas as pd
import numpy as np
import os
import joblib
import sys

import xgboost as xgb
import lightgbm as lgb

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


# Lettura dell'orizzonte temporale da linea di comando
# Esempio: python script.py --orizzonte=6
orizzonte = 1
for argomento in sys.argv:
    if "--orizzonte=" in argomento:
        orizzonte = int(argomento.split("=")[1])

print(f"\nTraining modelli ML per orizzonte T+{orizzonte}")


# Percorsi dataset
cartella_dataset = "dataset_intero/preparazione_dati/dataset_pronto_ml"

# Dataset specifico per l'orizzonte temporale selezionato
percorso_dataset = os.path.join(
    cartella_dataset,
    f"dataset_ml_T{orizzonte}.parquet"
)

# Cartella risultati
cartella_risultati = os.path.join(
    "dataset_intero",
    "machine_learning",
    "risultati"
)

os.makedirs(cartella_risultati, exist_ok=True)

# File CSV contenente le metriche finali
percorso_risultati = os.path.join(
    cartella_risultati,
    f"ml_risultati_T{orizzonte}.csv"
)

# Cartella per salvare i modelli addestrati
cartella_modelli = os.path.join(
    "dataset_intero",
    "machine_learning",
    f"T{orizzonte}"
)

os.makedirs(cartella_modelli, exist_ok=True)

print("Caricamento dataset...")
df = pd.read_parquet(percorso_dataset)
print("Dimensione dataset:", df.shape)


# Ordinamento temporale
# Fondamentale per garantire correttezza dello split temporale
if "valid_time" in df.columns:
    df = df.sort_values("valid_time")


# Faccio uno split temporale senza shuffle
# Evito data leakage mantenendo l'ordine cronologico
rapporto_train = 0.7
rapporto_validazione = 0.15

n = len(df)
indice_train = int(n * rapporto_train)
indice_val = int(n * (rapporto_train + rapporto_validazione))

df_train = df.iloc[:indice_train]
df_val = df.iloc[indice_train:indice_val]
df_test = df.iloc[indice_val:]

print("\nDimensioni split:")
print("Train:", len(df_train))
print("Validation:", len(df_val))
print("Test:", len(df_test))


# Variabili target (previsione multi-target indipendente)
variabili_target = [
    "u10", "v10", "t2m", "msl",
    "sst", "tcc", "tp_hourly",
    "swh", "pp1d"
]


# Feature base (tutte tranne metadati)
# NOTA: i target NON vengono rimossi qui, verranno esclusi per ogni target singolarmente
colonne_base = [
    colonna for colonna in df.columns
    if colonna not in ["region", "number", "expver", "valid_time"]
]

print("\nColonne base disponibili:")
print(colonne_base)


# Definizione dei modelli
def ottieni_modelli():
    return [
        ("XGBoost", xgb.XGBRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            tree_method="hist",
            random_state=42,
            n_jobs=-1
        )),
        ("LightGBM", lgb.LGBMRegressor(
            n_estimators=200,
            learning_rate=0.05,
            num_leaves=31,
            random_state=42,
            n_jobs=-1
        ))
    ]


risultati = []

# Viene fatto un loop su ogni target
# Ogni variabile viene prevista con un modello separato
for target in variabili_target:

    print("\nTarget corrente:", target)

    # Feature = tutte le colonne tranne il target corrente
    colonne_feature = [c for c in colonne_base if c != target]

    print("Feature usate:", colonne_feature)

    # Rimozione righe con target mancante
    train = df_train.dropna(subset=[target])
    val = df_val.dropna(subset=[target])
    test = df_test.dropna(subset=[target])

    print(f"Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")

    X_train = train[colonne_feature]
    y_train = train[target]

    X_test = test[colonne_feature]
    y_test = test[target]

    for nome_modello, modello_base in ottieni_modelli():

        print("\nAddestramento modello:", nome_modello)

        # Creazione nuova istanza del modello (evita contaminazioni tra target)
        modello = modello_base.__class__(**modello_base.get_params())

        modello.fit(X_train, y_train)

        # Predizione su test set
        pred = modello.predict(X_test)

        # Calcolo metriche
        rmse = np.sqrt(mean_squared_error(y_test, pred))
        mae = mean_absolute_error(y_test, pred)
        r2 = r2_score(y_test, pred)

        risultato = {
            "target": target,
            "modello": nome_modello,
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "orizzonte": orizzonte
        }

        print("Risultati:", risultato)
        risultati.append(risultato)

        print("Addestramento finale su train + validation")

        df_finale = pd.concat([train, val])

        X_finale = df_finale[colonne_feature]
        y_finale = df_finale[target]

        modello_finale = modello_base.__class__(**modello_base.get_params())
        modello_finale.fit(X_finale, y_finale)

        # Salvataggio modello
        nome_file = f"{nome_modello.lower()}_{target}.pkl"
        percorso_modello = os.path.join(cartella_modelli, nome_file)

        joblib.dump(modello_finale, percorso_modello)

        print("Modello salvato in:", percorso_modello)

df_risultati = pd.DataFrame(risultati)
df_risultati.to_csv(percorso_risultati, index=False)

print("\nTraining completato")
print("Risultati salvati in:", percorso_risultati)
