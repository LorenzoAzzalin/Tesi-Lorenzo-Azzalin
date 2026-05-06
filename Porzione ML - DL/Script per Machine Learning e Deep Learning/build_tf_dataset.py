import os
from dataset_lazy import create_tf_dataset


# Variabili usate dal modello
variabili_input = [
    "t2m", "sst",
    "u10", "v10",
    "msl", "tcc",
    "swh", "pp1d",
    "mwd_sin", "mwd_cos"
]

variabili_target = variabili_input.copy()


def crea_dataset_tf(percorso_train, percorso_val, dimensione_batch):
    """
    Costruisce i dataset TensorFlow per training e validazione.

    I dati vengono caricati in modalità lazy:
    - non vengono caricati completamente in RAM
    - vengono generati dinamicamente durante il training

    Questo approccio è fondamentale per dataset molto grandi.
    """

    if not os.path.exists(percorso_train):
        raise FileNotFoundError(f"File train non trovato: {percorso_train}")

    if not os.path.exists(percorso_val):
        raise FileNotFoundError(f"File validation non trovato: {percorso_val}")

    print("Dataset trovati correttamente")
    print("Train:", percorso_train)
    print("Validation:", percorso_val)

    dataset_train = create_tf_dataset(
        percorso_train,
        input_vars=variabili_input,
        target_vars=variabili_target,
        batch_size=dimensione_batch,
        window=72,
        repeat=True
    )

    dataset_val = create_tf_dataset(
        percorso_val,
        input_vars=variabili_input,
        target_vars=variabili_target,
        batch_size=dimensione_batch,
        window=72,
        repeat=False
    )

    return dataset_train, dataset_val
