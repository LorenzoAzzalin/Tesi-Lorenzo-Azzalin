import os
import numpy as np
import xarray as xr


# Percorsi della pipeline: si lavora sui dati già preprocessati
# per allineare le variabili ondose alla griglia meteorologica.
cartella_root = "dataset_intero"
cartella_preparazione = os.path.join(cartella_root, "preparazione_dati")

cartella_preprocessing = os.path.join(cartella_preparazione, "preprocessing")


# Funzione per preservare la componente temporale nei CSV.
# Utile per evitare perdita dell'informazione oraria durante l'esportazione.
def forza_datetime_per_csv(dataset, variabile_tempo="valid_time"):
    if variabile_tempo in dataset.coords:
        dataset = dataset.copy()
        dataset[variabile_tempo] = dataset[variabile_tempo].dt.strftime("%Y-%m-%d %H:%M:%S")
    return dataset


# Individuazione automatica delle regioni disponibili
regioni = [
    nome for nome in os.listdir(cartella_preprocessing)
    if os.path.isdir(os.path.join(cartella_preprocessing, nome))
]

print("Regioni trovate:", regioni)


for regione in regioni:

    print("\nRegione:", regione)

    cartella_regione = os.path.join(cartella_preprocessing, regione)

    cartella_meteo = os.path.join(cartella_regione, "meteo")
    cartella_onde = os.path.join(cartella_regione, "onde")

    # Verifica presenza dati necessari
    if not os.path.isdir(cartella_meteo) or not os.path.isdir(cartella_onde):
        print("Cartelle meteo/onde non trovate")
        continue

    # Lista dei file meteorologici (uno per mese)
    file_meteo_lista = sorted([
        f for f in os.listdir(cartella_meteo)
        if f.endswith("_meteo.nc")
    ])

    for file_meteo_nome in file_meteo_lista:

        nome_base = file_meteo_nome.replace("_meteo.nc", "")

        file_meteo = os.path.join(cartella_meteo, file_meteo_nome)
        file_onde = os.path.join(cartella_onde, f"{nome_base}_onde.nc")

        # Verifica che esista il file onde corrispondente
        if not os.path.isfile(file_onde):
            print("File onde non trovato:", file_onde)
            continue

        print("\nFile:", nome_base)

        parti_nome = nome_base.split("_")
        anno = parti_nome[-2]
        mese = parti_nome[-1]

        # Apertura dataset
        dataset_meteo = xr.open_dataset(file_meteo)
        dataset_onde = xr.open_dataset(file_onde)

        # La direzione delle onde è una variabile angolare.
        # Non può essere interpolata direttamente perché:
        # 0° e 360° rappresentano la stessa direzione ma sono numericamente distanti.
        # Si è risolta così:
        # 1. trasformazione in componenti cartesiane (coseno, seno)
        # 2. interpolazione delle componenti
        # 3. ricostruzione dell’angolo tramite arctan2
        if "mwd" in dataset_onde.data_vars:

            angolo = np.deg2rad(dataset_onde["mwd"])

            componente_u = np.cos(angolo)
            componente_v = np.sin(angolo)

            componente_u_interp = componente_u.interp(
                latitude=dataset_meteo.latitude,
                longitude=dataset_meteo.longitude,
                method="linear"
            )

            componente_v_interp = componente_v.interp(
                latitude=dataset_meteo.latitude,
                longitude=dataset_meteo.longitude,
                method="linear"
            )

            direzione_interp = (
                np.rad2deg(np.arctan2(componente_v_interp, componente_u_interp)) + 360
            ) % 360

        # Selezione delle variabili ondose diverse da mwd
        # (che è trattata separatamente)
        variabili_onde = [
            var for var in dataset_onde.data_vars
            if var != "mwd"
        ]

        # Interpolazione delle variabili ondose sulla griglia meteorologica
        # Questo passaggio è necessario perché:
        # - le onde e le variabili meteo hanno griglie diverse
        # - il modello richiede una griglia spaziale coerente
        dataset_onde_interp = dataset_onde[variabili_onde].interp(
            latitude=dataset_meteo.latitude,
            longitude=dataset_meteo.longitude,
            method="linear"
        )

        # Reintegrazione della direzione delle onde interpolata correttamente
        if "mwd" in dataset_onde.data_vars:
            dataset_onde_interp["mwd"] = direzione_interp

        # Pulizia encoding per evitare problemi nel salvataggio NetCDF
        for variabile in list(dataset_onde_interp.data_vars) + list(dataset_onde_interp.coords):
            dataset_onde_interp[variabile].encoding = {}

        # Salvataggio dataset allineato
        file_output = os.path.join(
            cartella_onde,
            f"{nome_base}_onde_allineate.nc"
        )

        dataset_onde_interp.to_netcdf(file_output)

        print("Creato:", file_output)

        # Esportazione CSV solo per gennaio (sample per debug/validazione)
        if mese == "01":

            dataset_csv = forza_datetime_per_csv(dataset_onde_interp)
            file_csv = file_output.replace(".nc", ".csv")

            dataset_csv.to_dataframe().reset_index().to_csv(file_csv, index=False)

            print("Creato CSV sample:", file_csv)

        # Chiusura dataset
        dataset_meteo.close()
        dataset_onde.close()
        dataset_onde_interp.close()


print("\nAllineamento onde completato")
