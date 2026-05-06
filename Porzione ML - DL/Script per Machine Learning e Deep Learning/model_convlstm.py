import tensorflow as tf


def crea_loss_mse_mascherata_pesata(pesi_variabili):
    """
    Crea una funzione di loss MSE che:
    - ignora automaticamente i valori NaN nel target
    - applica pesi diversi alle variabili

    pesi_variabili: lista di pesi (uno per ogni variabile prevista)
    """

    pesi_variabili = tf.constant(pesi_variabili, dtype=tf.float32)

    def loss(y_true, y_pred):

        # Creazione della maschera: 1 dove il dato è valido, 0 dove è NaN
        maschera = tf.math.is_finite(y_true)
        maschera = tf.cast(maschera, tf.float32)

        # Sostituzione dei NaN con 0 (non influenzeranno la loss grazie alla maschera)
        y_true_pulito = tf.where(tf.math.is_finite(y_true), y_true, 0.0)

        # Errore quadratico
        errore = tf.square(y_true_pulito - y_pred)

        # Applicazione dei pesi sulle variabili
        errore = errore * pesi_variabili

        # Applicazione della maschera
        errore = errore * maschera

        # Normalizzazione evitando divisioni per zero
        denominatore = tf.reduce_sum(maschera)
        denominatore = tf.maximum(denominatore, 1.0)

        return tf.reduce_sum(errore) / denominatore

    return loss


def mae_mascherata(y_true, y_pred):
    """
    Mean Absolute Error che ignora i NaN nel target.
    Utile come metrica interpretabile durante il training.
    """

    maschera = tf.math.is_finite(y_true)
    maschera = tf.cast(maschera, tf.float32)

    y_true_pulito = tf.where(tf.math.is_finite(y_true), y_true, 0.0)

    errore = tf.abs(y_true_pulito - y_pred)
    errore = errore * maschera

    denominatore = tf.reduce_sum(maschera)
    denominatore = tf.maximum(denominatore, 1.0)

    return tf.reduce_sum(errore) / denominatore


def costruisci_modello_convlstm(num_timesteps, lat, lon, num_variabili, funzione_loss):
    """
    Costruisce un modello ConvLSTM per previsioni spazio-temporali.

    Input:
    - sequenza temporale di mappe 2D (lat, lon) multivariate
    - ogni timestep contiene più variabili fisiche

    Output:
    - una mappa 2D multivariata prevista al tempo successivo
    """

    input_modello = tf.keras.Input(
        shape=(num_timesteps, lat, lon, num_variabili)
    )

    # Estrazione dinamica delle informazioni spazio-temporali
    x = tf.keras.layers.ConvLSTM2D(
        filters=16,
        kernel_size=(3, 3),
        padding="same",
        return_sequences=False
    )(input_modello)

    x = tf.keras.layers.BatchNormalization()(x)

    # Riduce overfitting mantenendo coerenza spaziale
    x = tf.keras.layers.SpatialDropout2D(0.2)(x)

    # Raffinamento spaziale
    x = tf.keras.layers.Conv2D(
        16,
        (3, 3),
        padding="same",
        activation="relu"
    )(x)

    x = tf.keras.layers.Conv2D(
        16,
        (3, 3),
        padding="same",
        activation="relu"
    )(x)

    # Output finale con stesso numero di variabili
    x = tf.keras.layers.Conv2D(
        num_variabili,
        (1, 1),
        padding="same"
    )(x)

    output = tf.keras.layers.Activation("linear")(x)

    modello = tf.keras.Model(input_modello, output)

    modello.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss=funzione_loss,
        metrics=[mae_mascherata]
    )

    return modello
