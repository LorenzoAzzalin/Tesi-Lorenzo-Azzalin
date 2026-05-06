import xarray as xr
import numpy as np
import tensorflow as tf


def create_tf_dataset(
    percorso_nc,
    variabili_input,
    variabili_target,
    window=72,
    stride=1,
    batch_size=1,
    repeat=True
):
    """
    Crea un dataset TensorFlow a partire da un file NetCDF.

    Il dataset viene generato in modalità lazy:
    - i dati non vengono caricati interamente in RAM
    - le sequenze vengono costruite dinamicamente durante il training

    Parametri:
    - percorso_nc: percorso del file NetCDF
    - variabili_input: lista variabili di input
    - variabili_target: lista variabili target
    - window: lunghezza della sequenza temporale
    - stride: passo tra una sequenza e la successiva
    - batch_size: dimensione del batch
    - repeat: se True, il dataset viene ciclato all’infinito
    """

    print("Apertura dataset NetCDF:", percorso_nc)

    dataset = xr.open_dataset(percorso_nc, chunks={})

    numero_timestep = dataset.sizes["valid_time"]

    print("Numero timestep:", numero_timestep)
    print("Lunghezza finestra temporale:", window)

    # Indici di partenza delle sequenze temporali
    # Ogni indice rappresenta l'inizio di una finestra temporale
    indici = np.arange(0, numero_timestep - window - 1, stride)

    def generatore():
        """
        Generatore Python che costruisce dinamicamente:
        - X: sequenza temporale (window, lat, lon, variabili)
        - y: target al tempo successivo (lat, lon, variabili)
        """

        for t in indici:

            # Costruzione input temporale
            X = dataset[variabili_input].isel(
                valid_time=slice(t, t + window)
            ).to_array().transpose(
                "valid_time", "latitude", "longitude", "variable"
            )

            # Costruzione target (timestep successivo)
            y = dataset[variabili_target].isel(
                valid_time=t + window
            ).to_array().transpose(
                "latitude", "longitude", "variable"
            )

            # Conversione in numpy float32
            X = X.astype("float32").values
            y = y.astype("float32").values

            # Controllo qualità dati
            # Se una finestra contiene troppi NaN viene scartata
            if np.isfinite(X).mean() < 0.2:
                continue

            if np.isfinite(y).mean() < 0.2:
                continue

            # Sostituzione NaN con 0
            # Le celle non valide verranno ignorate dalla loss mascherata
            X = np.nan_to_num(X, nan=0.0)

            yield X, y

    # Creazione dataset TensorFlow
    dataset_tf = tf.data.Dataset.from_generator(
        generatore,
        output_signature=(
            tf.TensorSpec(
                shape=(window, None, None, len(variabili_input)),
                dtype=tf.float32
            ),
            tf.TensorSpec(
                shape=(None, None, len(variabili_target)),
                dtype=tf.float32
            ),
        )
    )

    # Batch + prefetch per migliorare le prestazioni
    dataset_tf = dataset_tf.batch(batch_size).prefetch(1)

    # Se repeat=True, il dataset viene ciclato continuamente
    # Questo è necessario quando si usano step_per_epoch nel training
    return dataset_tf.repeat() if repeat else dataset_tf
