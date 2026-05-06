import os
import numpy as np
import xarray as xr
import tensorflow as tf
import pandas as pd
from sklearn.metrics import r2_score

# Import delle funzioni custom utilizzate nel training
# - mae_mascherata: metrica che ignora i NaN
# - loss mascherata pesata: coerente con quella usata in fase di training
from model_convlstm import mae_mascherata, crea_loss_mse_mascherata_pesata


# Regioni su cui eseguire la valutazione
regioni = ["atlantico", "pacifico", "indiano", "mediterraneo"]

# Percorsi principali
percorso_dataset = "dataset_intero/preparazione_dati/dataset_pronto_dl"
percorso_modelli = "dataset_intero/deep_learning/modelli"
percorso_output = "dataset_intero/deep_learning/risultati_convlstm.csv"

# Variabili utilizzate dal modello (devono coincidere con quelle del training)
variabili = [
    "t2m", "sst",
    "u10", "v10",
    "msl", "tcc",
    "swh", "pp1d",
    "mwd_sin", "mwd_cos"
]

# Lunghezza della finestra temporale (coerente con il training)
lunghezza_finestra = 72

# Stride tra una finestra e la successiva
# Riduce il numero di campioni valutati evitando ridondanza
stride = 10

# Lista che conterrà i risultati finali per tutte le regioni
risultati_globali = []


def trova_file_test(cartella_regione):

    # Ordine di priorità:
    # 1. test
    # 2. validation
    # 3. train (fallback)
    possibili_file = [
        "era5_test_scalato.nc",
        "era5_val_scalato.nc",
        "era5_train_scalato.nc"
    ]

    for nome_file in possibili_file:
        percorso = os.path.join(cartella_regione, nome_file)
        if os.path.exists(percorso):
            print(f"File utilizzato: {nome_file}")
            return percorso

    return None


def valuta_regione(nome_regione):

    print("\nValutazione regione:", nome_regione)

    cartella_regione = os.path.join(percorso_dataset, nome_regione)

    # Individuazione del dataset da utilizzare per la valutazione
    percorso_file = trova_file_test(cartella_regione)

    if percorso_file is None:
        print("Dataset non trovato")
        return

    print("Apertura dataset:", percorso_file)

    dataset = xr.open_dataset(percorso_file)
    numero_timestep = dataset.sizes["valid_time"]

    print("Numero timestep:", numero_timestep)

    # Percorso del modello addestrato
    percorso_modello = os.path.join(
        percorso_modelli,
        f"conv_lstm_72h_{nome_regione}.keras"
    )

    if not os.path.exists(percorso_modello):
        print("Modello non trovato")
        return

    print("Caricamento modello:", percorso_modello)

    # Ricostruzione della loss mascherata (necessaria per il caricamento del modello)
    funzione_loss = crea_loss_mse_mascherata_pesata([1] * len(variabili))

    modello = tf.keras.models.load_model(
        percorso_modello,
        custom_objects={
            "loss": funzione_loss,
            "mae_mascherata": mae_mascherata
        }
    )

    # Variabili per accumulare errori globali
    somma_mse = 0.0
    somma_mae = 0.0
    conteggio_valori = 0
    numero_step = 0

    # Liste per calcolo R² globale
    tutti_y_true = []
    tutti_y_pred = []

    # Scorrimento temporale con sliding window (coerente con training)
    for t in range(0, numero_timestep - lunghezza_finestra - 1, stride):

        if numero_step % 100 == 0:
            print(f"Step elaborati: {numero_step}")

        # Costruzione input (sequenza temporale)
        X = dataset[variabili].isel(
            valid_time=slice(t, t + lunghezza_finestra)
        ).to_array().transpose("valid_time", "latitude", "longitude", "variable")

        # Costruzione target (timestep successivo)
        y = dataset[variabili].isel(
            valid_time=t + lunghezza_finestra
        ).to_array().transpose("latitude", "longitude", "variable")

        # Conversione in float32
        X = X.astype("float32").values
        y = y.astype("float32").values

        # Salta esempi completamente privi di informazione
        if np.isfinite(y).sum() < 10:
            continue

        # Input: sostituzione NaN con 0
        # (coerente con training; i NaN verranno ignorati dalla loss)
        X = np.nan_to_num(X, nan=0.0)
        X = np.expand_dims(X, axis=0)

        # Predizione del modello
        y_pred = modello(X, training=False).numpy()[0]

        # Creazione maschera sui valori validi del target
        maschera = np.isfinite(y)

        # Sostituzione NaN con 0 solo per stabilità numerica
        y_pulito = np.where(maschera, y, 0.0)

        # Calcolo errori solo sulle celle valide
        errore_quadratico = ((y_pulito - y_pred) ** 2) * maschera
        errore_assoluto = np.abs(y_pulito - y_pred) * maschera

        somma_mse += np.sum(errore_quadratico)
        somma_mae += np.sum(errore_assoluto)
        conteggio_valori += np.sum(maschera)

        # Salvataggio valori validi per calcolo R^2 globale
        y_true_valid = y[maschera]
        y_pred_valid = y_pred[maschera]

        if y_true_valid.size > 0:
            tutti_y_true.append(y_true_valid)
            tutti_y_pred.append(y_pred_valid)

        numero_step += 1

    # Calcolo metriche finali
    rmse = np.sqrt(somma_mse / conteggio_valori)
    mae = somma_mae / conteggio_valori

    # Calcolo R² globale su tutti i valori validi
    if len(tutti_y_true) > 0:
        y_true_tot = np.concatenate(tutti_y_true)
        y_pred_tot = np.concatenate(tutti_y_pred)

        # Controllo robusto per evitare divisione per zero
        if y_true_tot.size > 100 and np.var(y_true_tot) > 1e-8:
            r2 = r2_score(y_true_tot, y_pred_tot)
        else:
            r2 = np.nan
    else:
        r2 = np.nan

    print("\nRisultati finali")
    print("Numero campioni:", numero_step)
    print(f"RMSE: {rmse:.4f}")
    print(f"MAE: {mae:.4f}")
    print(f"R2: {r2:.4f}" if not np.isnan(r2) else "R^2: non calcolabile")

    # Salvataggio risultati della regione
    risultati_globali.append({
        "regione": nome_regione,
        "modello": "convlstm",
        "rmse": rmse,
        "mae": mae,
        "r2": r2
    })


def main():

    # Loop su tutte le regioni
    for regione in regioni:
        valuta_regione(regione)

    # Creazione dataframe finale
    dataframe = pd.DataFrame(risultati_globali)

    os.makedirs(os.path.dirname(percorso_output), exist_ok=True)
    dataframe.to_csv(percorso_output, index=False)

    print("\nRisultati salvati in:")
    print(percorso_output)


if __name__ == "__main__":
    main()
