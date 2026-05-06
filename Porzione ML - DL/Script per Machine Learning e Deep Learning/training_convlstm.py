import os
import time
import tensorflow as tf
import xarray as xr

# Import del generatore lazy di dataset
# Questo modulo (dataset_lazy.py) è responsabile della costruzione dinamica
# delle sequenze temporali tramite sliding window, evitando il caricamento completo in memoria
from dataset_lazy import create_tf_dataset

# Import del modello ConvLSTM e della funzione di loss mascherata
from model_convlstm import costruisci_modello_convlstm, crea_loss_mse_mascherata_pesata


dimensione_batch = 1
numero_epoche = 10

# Lunghezza della finestra temporale 
lunghezza_finestra = 72

percorso_dataset = "dataset_intero/preparazione_dati/dataset_pronto_dl"
cartella_modelli = "dataset_intero/deep_learning/modelli"
os.makedirs(cartella_modelli, exist_ok=True)

# Variabili candidate per input e target
variabili_desiderate = [
    "t2m", "sst",
    "u10", "v10",
    "msl", "tcc",
    "swh", "pp1d",
    "mwd_sin", "mwd_cos"
]

os.makedirs(cartella_modelli, exist_ok=True)


# Configurazione GPU 
gpu_disponibili = tf.config.list_physical_devices('GPU')
if gpu_disponibili:
    tf.config.experimental.set_memory_growth(gpu_disponibili[0], True)

# Disabilitazione XLA per maggiore stabilità (è del tutto opzionale)
tf.config.optimizer.set_jit(False)


class CallbackStimaTempo(tf.keras.callbacks.Callback):

    # Callback personalizzata per stimare il tempo di training
    
    def on_train_begin(self, logs=None):
        self.inizio_training = time.time()
        self.tempi_epoche = []

    def on_epoch_begin(self, epoch, logs=None):
        self.inizio_epoca = time.time()

    def on_epoch_end(self, epoch, logs=None):

        tempo_epoca = time.time() - self.inizio_epoca
        self.tempi_epoche.append(tempo_epoca)

        tempo_medio = sum(self.tempi_epoche) / len(self.tempi_epoche)

        epoche_completate = epoch + 1
        epoche_rimanenti = self.params['epochs'] - epoche_completate

        eta = tempo_medio * epoche_rimanenti

        tempo_totale_trascorso = time.time() - self.inizio_training
        tempo_totale_stimato = tempo_medio * self.params['epochs']

        print("\nStima training")
        print(f"Epoca {epoche_completate}/{self.params['epochs']}")
        print(f"Tempo epoca: {tempo_epoca:.1f}s")
        print(f"Tempo medio: {tempo_medio:.1f}s")
        print(f"Tempo totale stimato: {tempo_totale_stimato/60:.1f} min")
        print(f"Tempo trascorso: {tempo_totale_trascorso/60:.1f} min")
        print(f"Tempo restante stimato: {eta/60:.1f} min\n")


def ottieni_variabili_disponibili(percorso_nc, variabili_desiderate):
    # Filtra le variabili realmente presenti nel dataset
    dataset = xr.open_dataset(percorso_nc)
    variabili = [v for v in variabili_desiderate if v in dataset.data_vars]
    dataset.close()
    return variabili


def ottieni_pesi_variabili(lista_variabili):

    # Definizione dei pesi per la loss
    # Permette di assegnare maggiore importanza a variabili fisicamente rilevanti
    pesi_base = {
        "t2m": 1.0,
        "sst": 1.0,
        "u10": 1.0,
        "v10": 1.0,
        "msl": 0.5,
        "tcc": 0.5,
        "swh": 1.0,
        "pp1d": 1.0,
        "mwd_sin": 0.8,
        "mwd_cos": 0.8
    }

    return [pesi_base[v] for v in lista_variabili]


def addestra_regione(regione):

    print("\nTraining regione:", regione)

    file_train = os.path.join(percorso_dataset, regione, "era5_train_scalato.nc")
    file_validazione = os.path.join(percorso_dataset, regione, "era5_val_scalato.nc")

    # Le variabili vengono selezionate in base alla loro presenza effettiva nel dataset
    variabili_input = ottieni_variabili_disponibili(file_train, variabili_desiderate)
    variabili_target = variabili_input.copy()

    print("Variabili utilizzate:", variabili_input)

    # Lettura numero timestep (serve per calcolo step_per_epoch)
    dataset_train = xr.open_dataset(file_train)
    numero_timestep = dataset_train.sizes["valid_time"]
    dataset_train.close()

    print("Numero timestep:", numero_timestep)
    print("Lunghezza finestra:", lunghezza_finestra)

    # Poiché il dataset è generato dinamicamente (repeat=True),
    # è necessario definire manualmente il numero di step per epoca
    step_per_epoca = max(10, (numero_timestep - lunghezza_finestra) // dimensione_batch // 50)
    step_validazione = max(5, step_per_epoca // 5)

    print("Step per epoca:", step_per_epoca)
    print("Step validazione:", step_validazione)

    # Creazione della loss mascherata pesata
    # Questa loss ignora le celle con valori mancanti (NaN),
    # permettendo di preservare la struttura spaziale senza introdurre imputazioni artificiali
    funzione_loss = crea_loss_mse_mascherata_pesata(
        ottieni_pesi_variabili(variabili_target)
    )

    # Qui viene utilizzata la funzione create_tf_dataset (dataset_lazy.py)
    # che costruisce sequenze temporali dinamicamente tramite sliding window
    # evitando il caricamento completo del dataset in memoria
    dataset_train_tf = create_tf_dataset(
        file_train,
        variabili_input,
        variabili_target,
        window=lunghezza_finestra,
        batch_size=dimensione_batch,
        repeat=True
    )

    dataset_val_tf = create_tf_dataset(
        file_validazione,
        variabili_input,
        variabili_target,
        window=lunghezza_finestra,
        batch_size=dimensione_batch,
        repeat=False
    )

    # Estrazione di un batch per determinare le dimensioni spaziali
    X_esempio, _ = next(iter(dataset_train_tf))

    lunghezza_seq = X_esempio.shape[1]
    latitudine = X_esempio.shape[2]
    longitudine = X_esempio.shape[3]

    print("Shape input:", X_esempio.shape)

    optimizer = tf.keras.optimizers.Adam(clipnorm=1.0)

    # Costruzione modello ConvLSTM
    # Il modello opera direttamente su dati spaziali (griglie lat-lon)
    modello = costruisci_modello_convlstm(
        lunghezza_seq,
        latitudine,
        longitudine,
        len(variabili_target),
        funzione_loss
    )

    modello.compile(optimizer=optimizer, loss=funzione_loss)

    callback = [
        CallbackStimaTempo(),
        tf.keras.callbacks.ReduceLROnPlateau(patience=2),
        tf.keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True)
    ]

    # Training del modello
    # Il dataset è infinito (repeat=True), quindi si usano steps_per_epoch
    modello.fit(
        dataset_train_tf,
        validation_data=dataset_val_tf,
        epochs=numero_epoche,
        steps_per_epoch=step_per_epoca,
        validation_steps=step_validazione,
        callbacks=callback,
        verbose=2
    )

    # Salvataggio modello
    percorso_salvataggio = os.path.join(
        cartella_modelli,
        f"conv_lstm_72h_{regione}.keras"
    )

    modello.save(percorso_salvataggio, include_optimizer=False)


def main():
    for regione in os.listdir(percorso_dataset):
        addestra_regione(regione)


if __name__ == "__main__":
    main()
