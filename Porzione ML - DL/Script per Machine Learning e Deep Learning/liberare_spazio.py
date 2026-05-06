import os
import shutil


cartella_radice = "dataset_intero"
cartella_preprocessing = os.path.join(cartella_radice, "preparazione_dati", "preprocessing")


print("\nPulizia dataset")


# eliminazione dati grezzi
percorso_dati_grezzi = os.path.join(cartella_radice, "dati_grezzi")

if os.path.isdir(percorso_dati_grezzi):
    try:
        shutil.rmtree(percorso_dati_grezzi)
        print("Cartella dati_grezzi eliminata")
    except Exception as errore:
        print("Errore eliminazione dati_grezzi:", errore)


# pulizia per ogni regione
if os.path.isdir(cartella_preprocessing):

    regioni = [
        nome for nome in os.listdir(cartella_preprocessing)
        if os.path.isdir(os.path.join(cartella_preprocessing, nome))
    ]

    print("\nRegioni trovate:", regioni)

    for regione in regioni:

        print("\nElaborazione regione:", regione)

        percorso_regione = os.path.join(cartella_preprocessing, regione)

        cartella_meteo = os.path.join(percorso_regione, "meteo")
        cartella_onde = os.path.join(percorso_regione, "onde")
        cartella_temporanei = os.path.join(percorso_regione, "temporanei")

        if os.path.isdir(cartella_meteo):
            try:
                shutil.rmtree(cartella_meteo)
                print("Cartella meteo eliminata")
            except Exception as errore:
                print("Errore eliminazione meteo:", errore)

        if os.path.isdir(cartella_onde):
            try:
                shutil.rmtree(cartella_onde)
                print("Cartella onde eliminata")
            except Exception as errore:
                print("Errore eliminazione onde:", errore)

        if os.path.isdir(cartella_temporanei):
            try:
                shutil.rmtree(cartella_temporanei)
                print("Cartella temporanei eliminata")
            except Exception as errore:
                print("Errore eliminazione temporanei:", errore)


print("\nPulizia completata")
