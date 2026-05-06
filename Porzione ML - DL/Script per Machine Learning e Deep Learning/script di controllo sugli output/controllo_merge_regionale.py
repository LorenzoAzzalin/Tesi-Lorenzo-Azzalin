import os
import xarray as xr
import numpy as np
import random

cartella_base = "dataset_intero/preparazione_dati/preprocessing"

NUM_TEST = 5

regioni = [
    r for r in os.listdir(cartella_base)
    if os.path.isdir(os.path.join(cartella_base, r))
]

print("Regioni trovate:", regioni)

for regione in regioni:

    print("\n==============================")
    print("Controllo regione:", regione)
    print("==============================")

    cartella_regione = os.path.join(cartella_base, regione)
    cartella_meteo = os.path.join(cartella_regione, "meteo")
    cartella_onde = os.path.join(cartella_regione, "onde")

    file_finale = os.path.join(cartella_regione, "dataset_regionale.nc")

    if not os.path.exists(file_finale):
        print("Dataset finale non trovato")
        continue

    ds_finale = xr.open_dataset(file_finale)

    print("\nDimensioni:", ds_finale.sizes)

    # Controllo continuità temporale
    tempi = ds_finale["valid_time"].values
    diff = np.diff(tempi).astype("timedelta64[h]").astype(int)

    if np.all(diff == diff[0]):
        print("Tempo OK")
    else:
        print("ATTENZIONE: buchi temporali")

    print("Variabili:", set(ds_finale.data_vars.keys()))

    # Recupero file meteo
    file_meteo = sorted([
        f for f in os.listdir(cartella_meteo)
        if f.endswith("_meteo.nc")
    ])

    if len(file_meteo) == 0:
        print("Nessun file meteo trovato")
        ds_finale.close()
        continue

    # Scelta casuale mese
    trovato = False

    for _ in range(len(file_meteo)):
        file_random = random.choice(file_meteo)
        nome_base = file_random.replace("_meteo.nc", "")

        percorso_meteo = os.path.join(cartella_meteo, file_random)
        percorso_onde = os.path.join(cartella_onde, f"{nome_base}_onde_allineate.nc")

        if os.path.exists(percorso_onde):
            trovato = True
            break

    if not trovato:
        print("Nessuna coppia meteo-onde valida trovata")
        ds_finale.close()
        continue

    print("\nConfronto con:", nome_base)

    ds_meteo = xr.open_dataset(percorso_meteo)
    ds_onde = xr.open_dataset(percorso_onde)

    ds_originale = xr.merge([ds_meteo, ds_onde])

    print("Confronto valori")

    variabili_test = list(ds_originale.data_vars.keys())[:4]

    for var in variabili_test:

        if var not in ds_finale:
            print(f"{var} non presente nel dataset finale")
            continue

        errori = []

        for t in range(min(NUM_TEST, ds_originale.sizes["valid_time"])):

            # Allineamento corretto tramite timestamp
            tempo = ds_originale["valid_time"].values[t]

            val_orig = ds_originale[var].isel(valid_time=t).values
            val_finale = ds_finale[var].sel(valid_time=tempo).values

            diff = np.nanmean(np.abs(val_orig - val_finale))
            errori.append(diff)

        errore_medio = np.mean(errori)

        print(f"{var} errore medio:", errore_medio)

        if errore_medio > 1e-5:
            print("ATTENZIONE: possibile disallineamento")

    ds_meteo.close()
    ds_onde.close()
    ds_originale.close()
    ds_finale.close()

print("\nValidazione completa terminata")
