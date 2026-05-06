import subprocess
import sys
import os

ESEGUIBILE_PYTHON = sys.executable


def esegui_script(nome_script):
    print("\n" + "=" * 70)
    print(f"ESECUZIONE: {nome_script}")
    print("=" * 70)

    punto_partenza = nome_script.split()

    script = punto_partenza[0]
    argomenti = punto_partenza[1:]

    if not os.path.isfile(script):
        print(f"ERRORE: script non trovato → {script}")
        sys.exit(1)

    risultato = subprocess.run(
        [ESEGUIBILE_PYTHON, script] + argomenti,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    if risultato.returncode != 0:
        raise RuntimeError(
            f"Esecuzione interrotta. Errore nello script: {script}"
        )


STEP_PIPELINE = [

    ("Creazione cartelle progetto", "creare_cartelle.py"),
    ("Download dataset meteo + onde", "download_dataset.py"),
    ("Unzip del dataset (instant + accum)", "unzip_dataset.py"),
    ("Regridding onde su griglia meteo", "regridding_onde.py"),
    ("Merge regionale meteo + onde", "merge_regionale.py"),
    ("Conversione unità variabili", "conversione_unita.py"),
    ("Maschera mare / terra", "maschera_terra_mare_temporale.py"),

    ("Feature engineering – step 1", "feature_engineering_step1.py"),
    ("Eliminazione dei file superflui", "liberare_spazio.py"),
    ("Feature cicliche – step 2", "feature_engineering_step2.py"),

    ("Split temporale", "split_temporale.py"),
    ("Calcolo scaler", "calcolo_scaler.py"),
    ("Applicazione scaler", "applica_scaler.py"),

    ("Training ConvLSTM", "training_convlstm.py"),
    ("Valutazione ConvLSTM", "valutazione_modelli_convlstm.py"),

    ("Flatten regionale", "flatten_regionale.py"),
    ("Preparazione dataset ML", "preparazione_dataset_ml.py"),
    ("Sampling ML", "creazione_sample_training_ml.py"),
    ("Dataset multi-horizon", "creazione_dataset_ml_multi_orizzonte.py"),

    ("Training ML T+1", "training_modelli_ml.py --orizzonte=1"),
    ("Training ML T+6", "training_modelli_ml.py --orizzonte=6"),
    ("Training ML T+12", "training_modelli_ml.py --orizzonte=12"),
    ("Training ML T+24", "training_modelli_ml.py --orizzonte=24"),

    ("Confronto ML vs DL", "confronto_risultati_ml_dl.py"),
    ("Valutazione e selezione modello", "valutazione_selezione_modello_migliore.py"),
    ("Inferenza e validazione finale", "inferenza_e_valutazione_finale.py"),
    ("Creazione modelli ML senza variabili lag per Android", "training_ml_modelli.py")
]


def main():
    print("\n" + "=" * 70)
    print("AVVIO PIPELINE")
    print("=" * 70)

    ripartenza_da = None

    if len(sys.argv) > 1:
        ripartenza_da = sys.argv[1]
        print(f"\nRipartenza da: {ripartenza_da}")

    indice_partenza = 0

    if ripartenza_da:

        trovato = False

        for indice, (_, nome_script) in enumerate(STEP_PIPELINE):

            if ripartenza_da in nome_script:
                indice_partenza = indice
                trovato = True
                break

        if not trovato:
            print(
                f"ERRORE: script '{ripartenza_da}' "
                f"non trovato nella pipeline"
            )
            sys.exit(1)

    for nome_step, nome_script in STEP_PIPELINE[indice_partenza:]:

        print("\n" + "-" * 70)
        print(f"STEP: {nome_step}")
        print("-" * 70)

        esegui_script(nome_script)

        print(f"\nCOMPLETATO: {nome_step}")

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETATA")
    print("=" * 70)


if __name__ == "__main__":
    main()
