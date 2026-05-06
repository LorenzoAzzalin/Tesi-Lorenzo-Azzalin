import pandas as pd
import numpy as np
import os
import joblib
import sys
import xgboost as xgb

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


# Lettura orizzonte da CLI (default = T+1)
orizzonte = 1
for argomento in sys.argv:
    if "--orizzonte=" in argomento:
        orizzonte = int(argomento.split("=")[1])

print(f"\nTraining modelli ML per orizzonte T+{orizzonte}")


# Percorsi
cartella_dataset = "dataset_intero/preparazione_dati/dataset_pronto_ml"

percorso_dataset = os.path.join(
    cartella_dataset,
    f"dataset_ml_T{orizzonte}.parquet"
)

if not os.path.exists(percorso_dataset):
    raise FileNotFoundError(f"Dataset non trovato: {percorso_dataset}")

cartella_modelli = os.path.join(
    "modelli_android",
    f"T{orizzonte}"
)

os.makedirs(cartella_modelli, exist_ok=True)


# Caricamento dataset
print("Caricamento dataset...")
df = pd.read_parquet(percorso_dataset)
print("Dimensione dataset:", df.shape)


# Ordinamento temporale
if "valid_time" in df.columns:
    df = df.sort_values("valid_time")


# Feature compatibili app
feature_finali = [
    "latitude",
    "longitude",
    "swh",
    "mwd_sin",
    "mwd_cos",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos"
]

feature_finali = [c for c in feature_finali if c in df.columns]

print("\nFeature utilizzate:")
print(feature_finali)


# Target
variabili_target = [
    "u10", "v10", "t2m", "msl",
    "sst", "tcc", "tp_hourly",
    "swh", "pp1d"
]


# Split temporale
n = len(df)
train_end = int(n * 0.7)
val_end = int(n * 0.85)

df_train = df.iloc[:train_end]
df_val = df.iloc[train_end:val_end]
df_test = df.iloc[val_end:]


# Modello XGBoost
def ottieni_modello():
    return xgb.XGBRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.05,
        tree_method="hist",
        random_state=42,
        n_jobs=-1
    )


# Training per ogni target
for target in variabili_target:

    if target not in df.columns:
        print("Target non presente:", target)
        continue

    print("\nTarget:", target)

    train = df_train.dropna(subset=[target] + feature_finali)
    val = df_val.dropna(subset=[target] + feature_finali)
    test = df_test.dropna(subset=[target] + feature_finali)

    X_train = train[feature_finali]
    y_train = train[target]

    X_test = test[feature_finali]
    y_test = test[target]

    modello = ottieni_modello()
    modello.fit(X_train, y_train)

    pred = modello.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, pred))
    mae = mean_absolute_error(y_test, pred)
    r2 = r2_score(y_test, pred)

    print(f"RMSE:{rmse:.3f} MAE:{mae:.3f} R2:{r2:.3f}")

    # training finale
    df_finale = pd.concat([train, val])

    modello_finale = ottieni_modello()
    modello_finale.fit(
        df_finale[feature_finali],
        df_finale[target]
    )

    percorso_modello = os.path.join(
        cartella_modelli,
        f"xgboost_{target}.pkl"
    )

    joblib.dump(modello_finale, percorso_modello)

    print("Salvato:", percorso_modello)


print("\nTraining completato")
