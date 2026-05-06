# Script eseguito per la creazione di un server locale
# in grado di rispondere alle richieste android
import os
import joblib
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_PATH = os.path.join("dataset per android")

TARGETS = [
    "u10", "v10", "t2m", "msl",
    "sst", "tcc", "tp_hourly",
    "swh", "pp1d"
]

FEATURE_ORDER = [
    "latitude",
    "longitude",
    "swh",
    "mwd_sin",
    "mwd_cos",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos"
]

modelli_cache = {}


def carica_modelli(orizzonte):

    chiave = f"T{orizzonte}"

    if chiave in modelli_cache:
        return modelli_cache[chiave]

    path = os.path.join(BASE_PATH, chiave)

    if not os.path.exists(path):
        raise ValueError(f"Orizzonte non disponibile: T{orizzonte}")

    modelli = {}

    for target in TARGETS:
        file_path = os.path.join(path, f"xgboost_{target}.pkl")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Modello mancante: {file_path}")

        modelli[target] = joblib.load(file_path)

    modelli_cache[chiave] = modelli
    return modelli


@app.route("/predict", methods=["POST"])
def predict():

    data = request.json

    if data is None:
        return jsonify({"errore": "JSON non valido"}), 400

    missing = [f for f in FEATURE_ORDER if f not in data]
    if missing:
        return jsonify({
            "errore": "Feature mancanti",
            "mancanti": missing
        }), 400

    try:
        horizon = int(data.get("horizon", 1))

        if horizon not in [1, 6, 12, 24]:
            return jsonify({"errore": "Orizzonte non valido"}), 400

        features = np.array(
            [data[f] for f in FEATURE_ORDER],
            dtype=np.float32
        ).reshape(1, -1)

        modelli = carica_modelli(horizon)

        risultati = {}

        for target, modello in modelli.items():
            risultati[target] = float(modello.predict(features)[0])

        return jsonify({"predictions": risultati})

    except Exception as e:
        return jsonify({"errore": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
