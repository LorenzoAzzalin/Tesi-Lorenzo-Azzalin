"""
Crea la struttura del progetto organizzando separatamente:
- fase di preparazione dei dati
- pipeline di Deep Learning
- pipeline di Machine Learning

La separazione logica delle componenti consente di mantenere il progetto modulare,
facilitare il debugging e permettere il confronto tra approcci diversi.
"""

import os
import subprocess


# Funzione di utilità per la creazione di cartelle.
# Garantisce che tutte le directory necessarie esistano,
# evitando errori in esecuzioni ripetute della pipeline.
def crea_cartella(percorso: str):
    os.makedirs(percorso, exist_ok=True)
    print(f"Cartella pronta: {percorso}")


# Creazione di un collegamento simbolico (junction su Windows) tra
# la directory del progetto e la posizione reale del dataset.
# Questo approccio consente la memorizzazione degli script su ssd e
# l'archiviazione dei loro output (di gran lunga più voluminosa) su hdd (molto capiente)
def crea_link(percorso_link, percorso_reale):
    if not os.path.exists(percorso_link):
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", percorso_link, percorso_reale],
            check=True
        )
        print(f"Link creato: {percorso_link} -> {percorso_reale}")
    else:
        print("Link già esistente")


def main():

    print("Creazione struttura progetto ML")

    # Directory principale del progetto (working directory corrente).
    # Tutti i percorsi relativi vengono costruiti a partire da questa posizione.
    directory_progetto = os.getcwd()
    print(f"Root progetto: {directory_progetto}")

    # Cartella dedicata ai modelli esportati per Android.
    # Conterrà eventuali modelli convertiti in ONNX, TensorFlow Lite
    # o altri formati utilizzabili direttamente nell'app mobile.
    cartella_modelli_android = os.path.join(
        directory_progetto,
        "modelli_android"
    )

crea_cartella(cartella_modelli_android)

    # Percorso fisico del dataset.
    # Il dataset viene salvato fuori dal progetto per evitare problemi di spazio
    # e per consentire un riutilizzo indipendente dalla struttura del codice.
    percorso_dataset_reale = r"D:\dataset_intero"
    crea_cartella(percorso_dataset_reale)

    # Creazione del link simbolico al dataset all'interno del progetto
    percorso_link = os.path.join(directory_progetto, "dataset_intero")
    crea_link(percorso_link, percorso_dataset_reale)

    # Definizione delle regioni oceanografiche considerate nel progetto.
    # Ogni regione viene trattata in modo indipendente nella pipeline.
    regioni = [
        "mediterraneo",
        "atlantico",
        "pacifico",
        "indiano",
    ]

    # Struttura della fase di preparazione dati:
    # - dati_grezzi: dati originali scaricati
    # - preprocessing: dati puliti e allineati
    # - feature_engineering: dataset arricchiti con nuove feature
    # - dataset_pronto_dl: dataset finali per Deep Learning
    # - dataset_pronto_ml: dataset tabellari per Machine Learning
    prep_root = os.path.join(percorso_dataset_reale, "preparazione_dati")

    prep_grezzi = os.path.join(prep_root, "dati_grezzi")
    prep_preproc = os.path.join(prep_root, "preprocessing")
    prep_feature = os.path.join(prep_root, "feature_engineering")
    prep_dl = os.path.join(prep_root, "dataset_pronto_dl")
    prep_ml = os.path.join(prep_root, "dataset_pronto_ml")

    # Creazione delle cartelle principali della pipeline dati.
    # Questa organizzazione riflette le diverse fasi di trasformazione del dataset.
    for cartella in [
        prep_root,
        prep_grezzi,
        prep_preproc,
        prep_feature,
        prep_dl,
        prep_ml
    ]:
        crea_cartella(cartella)

    # Creazione delle sottocartelle per ogni regione.
    # Permette di gestire separatamente i dati geografici 
    for regione in regioni:
        crea_cartella(os.path.join(prep_grezzi, regione))
        crea_cartella(os.path.join(prep_preproc, regione))
        crea_cartella(os.path.join(prep_feature, regione))
        crea_cartella(os.path.join(prep_dl, regione))

    # Struttura dedicata ai risultati del Deep Learning:
    # - modelli: modelli addestrati
    # - risultati: metriche e output di valutazione
    dl_root = os.path.join(percorso_dataset_reale, "deep_learning")

    dl_modelli = os.path.join(dl_root, "modelli")
    dl_risultati = os.path.join(dl_root, "risultati")

    for cartella in [dl_root, dl_modelli, dl_risultati]:
        crea_cartella(cartella)

    # Struttura dedicata al Machine Learning classico.
    # I risultati vengono separati per mantenere indipendente questa pipeline.
    ml_root = os.path.join(percorso_dataset_reale, "machine_learning")

    ml_risultati = os.path.join(ml_root, "risultati")

    for cartella in [ml_root, ml_risultati]:
        crea_cartella(cartella)

    # Creazione di sottocartelle per ciascun orizzonte temporale di previsione (T+1, T+6, ecc.).
    # Questa organizzazione consente di confrontare facilmente le prestazioni
    # dei modelli al variare dell’orizzonte temporale.
    for orizzonte in [1, 6, 12, 24]:
        crea_cartella(os.path.join(ml_root, f"T{orizzonte}"))

    # Creazione di file di supporto nella root del progetto.
    # README.md: documentazione del progetto
    # requisiti.txt: dipendenze software utilizzate
    file_supporto = [
        os.path.join(directory_progetto, "README.md"),
        os.path.join(directory_progetto, "requisiti.txt"),
    ]

    for file_path in file_supporto:
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("")
            print(f"Creato: {file_path}")

    # Messaggi finali di riepilogo:
    # - percorso reale del dataset
    # - percorso di accesso tramite link simbolico
    print("\nStruttura completata")
    print("Dataset reale:", percorso_dataset_reale)
    print("Accesso tramite link:", percorso_link)


if __name__ == "__main__":
    main()
