package com.example.progettotesi;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class InterfacciaWebJavaScript {
    private static final String TAG = "WebAppInterface";
    private DatabaseLocale database;
    private Context contesto;

    public InterfacciaWebJavaScript(Context context) {

        this.contesto = context;

        /* Inizializzazione del database Room tramite Singleton */
        database = DatabaseLocale.ottieniIstanza(context);

        Log.d(TAG, "Database Room inizializzato");
    }

    /* Metodo chiamato da JavaScript per ricevere i dati meteo */
    @JavascriptInterface
    public void riceviDati(String lat, String lon, String meteoJson) {

        try {
            JSONObject root = new JSONObject(meteoJson);

            if (!root.has("current")) {
                Log.e(TAG, "JSON senza campo 'current'");
                return;
            }

            JSONObject current = root.getJSONObject("current");

            String corpoMarino = null;
            if (root.has("localita") && !root.isNull("localita")) {
                corpoMarino = root.getString("localita");
            }

            DatiMarini dati = new DatiMarini();

            dati.corpo_marino = corpoMarino;
            dati.latitudine = parseDoubleSafe(lat);
            dati.longitudine = parseDoubleSafe(lon);
            dati.altezza_onda = getDoubleOrNull(current, "wave_height");
            dati.direzione_onda = getDoubleOrNull(current, "wave_direction");
            dati.altezza_onda_vento = getDoubleOrNull(current, "wind_wave_height");
            dati.direzione_onda_vento = getDoubleOrNull(current, "wind_wave_direction");
            dati.periodo_onda_vento = getDoubleOrNull(current, "wind_wave_period");
            dati.temperatura_superficie_mare =
                    getDoubleOrNull(current, "sea_surface_temperature");
            dati.livello_mare_msl =
                    getDoubleOrNull(current, "sea_level_height_msl");
            dati.direzione_corrente_oceanica =
                    getDoubleOrNull(current, "ocean_current_direction");
            dati.velocita_corrente_oceanica =
                    getDoubleOrNull(current, "ocean_current_velocity");
            dati.timestamp = System.currentTimeMillis();
            database.datiMariniDao().insert(dati);
            Log.d(TAG, "Dati salvati correttamente in Room");

        } catch (Exception e) {
            Log.e(TAG, "Errore nel parsing del JSON", e);
        }
    }

    /* Porzione relativa al modello ML */

    @JavascriptInterface
    public void riceviCoordinate(String json) {

        try {

            JSONObject obj = new JSONObject(json);

            double lat = obj.getDouble("latitude");
            double lon = obj.getDouble("longitude");

            double mwd = obj.getDouble("mwd");

            double swh_lag_1 = obj.getDouble("swh_lag_1");
            double swh_lag_3 = obj.getDouble("swh_lag_3");

            double u10_lag_1 = obj.getDouble("u10_lag_1");
            double u10_lag_3 = obj.getDouble("u10_lag_3");

            double v10_lag_1 = obj.getDouble("v10_lag_1");
            double v10_lag_3 = obj.getDouble("v10_lag_3");

            int hour = obj.getInt("hour");
            int month = obj.getInt("month");

            apriSelettoreOrizzonte(
                    lat, lon, mwd,
                    swh_lag_1, swh_lag_3,
                    u10_lag_1, u10_lag_3,
                    v10_lag_1, v10_lag_3,
                    hour, month
            );

        } catch (Exception e) {
            Log.e(TAG, "Errore parsing coordinate", e);
        }
    }

    private void apriSelettoreOrizzonte(
            double lat, double lon,
            double mwd,
            double swh_lag_1, double swh_lag_3,
            double u10_lag_1, double u10_lag_3,
            double v10_lag_1, double v10_lag_3,
            int hour, int month
    ) {

        String[] opzioni = {
                "Previsione tra 1 ora",
                "Previsione tra 6 ore",
                "Previsione tra 12 ore",
                "Previsione tra 24 ore"
        };

        int[] orizzonti = {1, 6, 12, 24};

        new AlertDialog.Builder(contesto)
                .setTitle("Seleziona orizzonte previsione")
                .setItems(opzioni, (dialog, which) -> {

                    int ore = orizzonti[which];

                    sendPredictionRequest(
                            lat, lon, mwd,
                            swh_lag_1, swh_lag_3,
                            u10_lag_1, u10_lag_3,
                            v10_lag_1, v10_lag_3,
                            hour, month,
                            ore
                    );
                })
                .show();
    }

    private void sendPredictionRequest(
            double lat, double lon,
            double mwd,
            double swh_lag_1, double swh_lag_3,
            double u10_lag_1, double u10_lag_3,
            double v10_lag_1, double v10_lag_3,
            int hour, int month,
            int ore
    ) {

        new Thread(() -> {

            try {

                URL url = new URL("https://web-production-c9ec0.up.railway.app/predict");

                HttpURLConnection conn = (HttpURLConnection) url.openConnection();

                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);

                JSONObject requestJson = new JSONObject();

                requestJson.put("latitude", lat);
                requestJson.put("longitude", lon);
                requestJson.put("mwd", mwd);
                requestJson.put("swh_lag_1", swh_lag_1);
                requestJson.put("swh_lag_3", swh_lag_3);
                requestJson.put("u10_lag_1", u10_lag_1);
                requestJson.put("u10_lag_3", u10_lag_3);
                requestJson.put("v10_lag_1", v10_lag_1);
                requestJson.put("v10_lag_3", v10_lag_3);
                requestJson.put("hour", hour);
                requestJson.put("month", month);
                requestJson.put("horizon", ore);

                OutputStream os = conn.getOutputStream();
                os.write(requestJson.toString().getBytes());
                os.flush();
                os.close();

                BufferedReader br = new BufferedReader(
                        new InputStreamReader(conn.getInputStream())
                );

                StringBuilder response = new StringBuilder();
                String line;

                while ((line = br.readLine()) != null) {
                    response.append(line);
                }

                br.close();

                JSONObject json = new JSONObject(response.toString());

                RisultatoPrevisione pred = parsePredizione(json);

                String messaggio = costruisciMessaggioPrevisione(pred, lat, lon, ore);

                mostraPopup(messaggio);

            } catch (Exception e) {

                Log.e(TAG, "Errore chiamata API ML", e);

                ((Activity) contesto).runOnUiThread(() ->
                        Toast.makeText(contesto,
                                "Connessione al modello non disponibile",
                                Toast.LENGTH_LONG).show()
                );
            }

        }).start();
    }

    private RisultatoPrevisione parsePredizione(JSONObject json) throws Exception {

        JSONObject predictions = json.getJSONObject("predictions");

        RisultatoPrevisione pred = new RisultatoPrevisione();

        pred.swh = predictions.optDouble("swh", 0);
        pred.u10 = predictions.optDouble("u10", 0);
        pred.v10 = predictions.optDouble("v10", 0);
        pred.t2m = predictions.optDouble("t2m", 0);
        pred.tcc = predictions.optDouble("tcc", 0);

        return pred;
    }

    private String costruisciMessaggioPrevisione(
            RisultatoPrevisione pred,
            double lat,
            double lon,
            int ore
    ) {

        double vento = Math.sqrt(pred.u10 * pred.u10 + pred.v10 * pred.v10);

        return "Coordinate: " + lat + ", " + lon + "\n\n" +
                "Previsione tra " + ore + " ore\n\n" +
                "Altezza onda: " + pred.swh + " m\n" +
                "Velocità vento: " + vento + " m/s\n" +
                "Temperatura aria: " + pred.t2m + " °C\n" +
                "Copertura nuvole: " + (pred.tcc * 100) + " %";
    }

    private void mostraPopup(String messaggio) {

        ((Activity) contesto).runOnUiThread(() -> {
            new AlertDialog.Builder(contesto)
                    .setTitle("Previsione Marina")
                    .setMessage(messaggio)
                    .setPositiveButton("OK", null)
                    .show();
        });
    }


    /* Metodo per ottenere un Double dal JSON */
    private Double getDoubleOrNull(JSONObject obj, String key) {
        if (!obj.has(key) || obj.isNull(key)) {
            return null;
        }
        try {
            return obj.getDouble(key);
        } catch (Exception e) {
            return null;
        }
    }

    /* Metodo per convertire String in Double */
    private Double parseDoubleSafe(String value) {
        try {
            return Double.parseDouble(value);
        } catch (Exception e) {
            return null;
        }
    }
}