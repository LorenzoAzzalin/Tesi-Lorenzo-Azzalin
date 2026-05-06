package com.example.progettotesi;

import android.app.Activity;
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


/*
Questa classe rappresenta il punto di collegamento tra JavaScript (mappa) e codice Java.
Flusso:
1) L’utente clicca sulla mappa
2) Il JavaScript genera le feature (sin/cos, ecc.)
3) Le invia a questo bridge tramite JSON
4) Il backend esegue il modello ML
5) Il risultato torna qui e viene mostrato all’utente
*/
public class InterfacciaWebJavaScript {
    /* Tag utilizzato per i log Android */
    private static final String TAG_LOG = "ML_APP";
    private Context contesto;

    public InterfacciaWebJavaScript(Context contesto) {
        this.contesto = contesto;
    }

    /*
    Metodo chiamato direttamente dal JavaScript.
    Riceve:
    - coordinate geografiche
    - feature temporali cicliche
    - dati marini correnti
    Dopo il parsing, i dati vengono inviati al backend Flask.
    */
    @JavascriptInterface
    public void riceviCoordinate(String jsonDati) {
        try {
            /* Conversione della stringa JSON in oggetto JSON */
            JSONObject oggettoJson = new JSONObject(jsonDati);
            /* Coordinate geografiche */
            double latitudine = oggettoJson.getDouble("latitude");
            double longitudine = oggettoJson.getDouble("longitude");

            /* Stato attuale del mare */
            double swh = oggettoJson.getDouble("swh");

            /* Direzione onde trasformata in sin/cos */
            double mwd_sin = oggettoJson.getDouble("mwd_sin");
            double mwd_cos = oggettoJson.getDouble("mwd_cos");

            /* Informazioni temporali cicliche */
            double hour_sin = oggettoJson.getDouble("hour_sin");
            double hour_cos = oggettoJson.getDouble("hour_cos");

            double month_sin = oggettoJson.getDouble("month_sin");
            double month_cos = oggettoJson.getDouble("month_cos");

            /* Orizzonte temporale selezionato nell'app */
            int oriz = MappaPrevisioni.ORIZZONTE;

            /* Invio richiesta HTTP al backend Flask */
            inviaRichiestaPrevisione(
                    latitudine,
                    longitudine,
                    swh,
                    mwd_sin,
                    mwd_cos,
                    hour_sin,
                    hour_cos,
                    month_sin,
                    month_cos,
                    oriz
            );
        } catch (Exception errore) {
            Log.e(TAG_LOG, "Errore parsing JSON ML", errore);
        }
    }

    /* Questo metodo esegue la chiamata HTTP al backend Flask*/
    private void inviaRichiestaPrevisione(
            double latitudine,
            double longitudine,
            double swh,
            double mwd_sin,
            double mwd_cos,
            double hour_sin,
            double hour_cos,
            double month_sin,
            double month_cos,
            int horizon) {
        new Thread(() -> {
            try {
                /* URL del backend Flask */
                URL url = new URL("http://10.0.2.2:5000/predict");

                /* Apertura connessione HTTP */
                HttpURLConnection connessione = (HttpURLConnection) url.openConnection();
                connessione.setRequestMethod("POST");
                connessione.setRequestProperty("Content-Type", "application/json");
                connessione.setDoOutput(true);
                connessione.setConnectTimeout(5000);
                connessione.setReadTimeout(5000);

                /* Costruzione payload JSON */
                JSONObject jsonRichiesta = new JSONObject();
                jsonRichiesta.put("latitude", latitudine);
                jsonRichiesta.put("longitude", longitudine);
                jsonRichiesta.put("swh", swh);
                jsonRichiesta.put("mwd_sin", mwd_sin);
                jsonRichiesta.put("mwd_cos", mwd_cos);
                jsonRichiesta.put("hour_sin", hour_sin);
                jsonRichiesta.put("hour_cos", hour_cos);
                jsonRichiesta.put("month_sin", month_sin);
                jsonRichiesta.put("month_cos", month_cos);
                jsonRichiesta.put("horizon", horizon);

                /* Invio del payload al backend */
                OutputStream streamOutput = connessione.getOutputStream();
                streamOutput.write(jsonRichiesta.toString().getBytes());

                streamOutput.flush();
                streamOutput.close();

                /* Recupero codice risposta HTTP */
                int codiceRisposta = connessione.getResponseCode();

                /* Lettura della risposta del backend */
                InputStreamReader lettoreInput =
                        (codiceRisposta >= 200 && codiceRisposta < 300)
                                ? new InputStreamReader(
                                connessione.getInputStream()
                        )
                                : new InputStreamReader(
                                connessione.getErrorStream()
                        );

                BufferedReader lettoreBuffer = new BufferedReader(lettoreInput);

                StringBuilder risposta = new StringBuilder();

                String riga;
                while ((riga = lettoreBuffer.readLine()) != null) {
                    risposta.append(riga);
                }
                lettoreBuffer.close();

                Log.d(TAG_LOG, "RISPOSTA BACKEND: " + risposta);

                /* Verifica che il backend abbia restituito dati */
                if (risposta.length() == 0) {
                    throw new RuntimeException(
                            "Risposta backend vuota"
                    );
                }

                /* Conversione risposta backend in JSON */
                JSONObject jsonDati = new JSONObject(risposta.toString());

                /* Analisi della previsione restituita dal modello */
                RisultatoPrevisione previsione = analizzaPrevisione(jsonDati);

                /* Salvataggio della previsione nel database */
                salvaPrevisioneSuDatabase(previsione, latitudine, longitudine);

                /* Costruzione messaggio finale */
                String messaggio = costruisciMessaggioPrevisione(previsione, latitudine,
                        longitudine, horizon);

                /* Visualizzazione popup previsione */
                mostraPopupPrevisione(messaggio);

                /* Sblocco della variabile JavaScript che impedisce
                click multipli simultanei*/

                ((Activity) contesto).runOnUiThread(() -> {
                    android.webkit.WebView webViewMappaML =
                            ((Activity) contesto).findViewById(R.id.webViewMappaML);

                    webViewMappaML.evaluateJavascript("richiestaInCorso = false;", null);
                });
            } catch (Exception errore) {
                Log.e(TAG_LOG, "Errore chiamata backend ML", errore);
                /* Mostra errore all'utente */
                ((Activity) contesto).runOnUiThread(() ->
                        Toast.makeText(contesto, "Errore connessione modello", Toast.LENGTH_LONG
                        ).show()
                );
            }
        }).start();
    }

    /* Analizza la risposta JSON restituita dal modello ML */
    private RisultatoPrevisione analizzaPrevisione(JSONObject jsonDati) {

        RisultatoPrevisione risultato = new RisultatoPrevisione();

        try {
            /* Recupera il blocco predictions */
            JSONObject previsioniJson = jsonDati.getJSONObject("predictions");

            /* Estrazione variabili previste dal modello */
            risultato.swh = previsioniJson.optDouble("swh", 0);
            risultato.u10 = previsioniJson.optDouble("u10", 0);
            risultato.v10 = previsioniJson.optDouble("v10", 0);
            risultato.t2m = previsioniJson.optDouble("t2m", 0);
            risultato.msl = previsioniJson.optDouble("msl", 0);
            risultato.sst = previsioniJson.optDouble("sst", 0);
            risultato.tcc = previsioniJson.optDouble("tcc", 0);
            risultato.tp_hourly = previsioniJson.optDouble("tp_hourly", 0);
            risultato.pp1d = previsioniJson.optDouble("pp1d", 0);
        } catch (Exception errore) {
            Log.e(TAG_LOG, "Errore parsing risposta", errore);
        }
        return risultato;
    }

    /*
    Costruisce il messaggio mostrato nel popup finale.
    */
    private String costruisciMessaggioPrevisione(
            RisultatoPrevisione previsione,
            double latitudine, double longitudine, int ore) {

        return "Previsione T+" + ore + "h\n\n" +

                "Lat: " +
                String.format("%.2f", latitudine) +

                "\nLon: " +
                String.format("%.2f", longitudine) +

                "\n\nOnde: " +
                String.format("%.2f m", previsione.swh) +

                "\nVento u10: " +
                String.format("%.2f m/s", previsione.u10) +

                "\nVento v10: " +
                String.format("%.2f m/s", previsione.v10) +

                "\nTemp aria: " +
                String.format("%.2f °C", previsione.t2m) +

                "\nTemp mare: " +
                String.format("%.2f °C", previsione.sst) +

                "\nPressione: " +
                String.format("%.0f hPa", previsione.msl);
    }


    // Mostra il popup finale contenente la previsione ML
    private void mostraPopupPrevisione(String messaggio) {
        new android.os.Handler(android.os.Looper.getMainLooper()).post(() -> {
            new android.app.AlertDialog.Builder(contesto)
                    .setTitle("Previsione meteo-marina (ML)")
                    .setMessage(messaggio)
                    .setPositiveButton("OK", null)
                    .show();
        });
    }

    /* Salvataggio della previsione ML nel database locale */
    private void salvaPrevisioneSuDatabase(
            RisultatoPrevisione previsione,
            double latitudine, double longitudine) {

        try {
            /* Recupero istanza database Room */
            DatabaseLocale databaseLocale = DatabaseLocale.ottieniIstanza(contesto);

            /* Creazione nuovo oggetto dati */
            DatiMarini datiMarini = new DatiMarini();
            /* Coordinate geografiche */
            datiMarini.latitudine = latitudine;
            datiMarini.longitudine = longitudine;

            /* Variabili previste dal modello ML */
            datiMarini.altezza_onda = previsione.swh;
            datiMarini.u10 = previsione.u10;
            datiMarini.v10 = previsione.v10;
            datiMarini.t2m = previsione.t2m;
            datiMarini.livello_mare_msl = previsione.msl;
            datiMarini.temperatura_superficie_mare = previsione.sst;

            /* Tipo sorgente dei dati */
            datiMarini.tipo_sorgente = "ML";

            // Timestamp corrente per sapere a quando risale l'informazione
            datiMarini.timestamp = System.currentTimeMillis();

            /* Inserimento nel database */
            databaseLocale.datiMariniDao().insert(datiMarini);
        } catch (Exception errore) {
            Log.e("DB", "Errore salvataggio ML", errore);
        }
    }

    /* Metodo utilizzato dalla mappa API classica
    per salvare i dati marini nel database. */
    @JavascriptInterface
    public void riceviDati(
            String latitudineStringa,
            String longitudineStringa,
            String jsonDati) {

        try {
            /* Conversione coordinate */
            double latitudine = Double.parseDouble(latitudineStringa);
            double longitudine = Double.parseDouble(longitudineStringa);

            /* Conversione JSON */
            JSONObject oggettoJson = new JSONObject(jsonDati);

            /* Recupero blocco current */
            JSONObject datiCorrenti = oggettoJson.optJSONObject("current");
            if (datiCorrenti == null) {
                Log.e("API", "Campo 'current' mancante");
                return;
            }

            /* Recupero database Room */
            DatabaseLocale databaseLocale = DatabaseLocale.ottieniIstanza(contesto);
            /* Creazione oggetto dati */
            DatiMarini datiMarini = new DatiMarini();
            /* Nome corpo marino */
            datiMarini.corpo_marino =
                    oggettoJson.optString("localita", null);

            /* Coordinate */
            datiMarini.latitudine = latitudine;
            datiMarini.longitudine = longitudine;

            /* Variabili marine */
            datiMarini.altezza_onda =
                    datiCorrenti.optDouble("wave_height", Double.NaN);

            datiMarini.direzione_onda =
                    datiCorrenti.optDouble("wave_direction", Double.NaN);

            datiMarini.altezza_onda_vento =
                    datiCorrenti.optDouble("wind_wave_height", Double.NaN);

            datiMarini.direzione_onda_vento =
                    datiCorrenti.optDouble("wind_wave_direction", Double.NaN);

            datiMarini.periodo_onda_vento =
                    datiCorrenti.optDouble("wind_wave_period", Double.NaN);

            datiMarini.temperatura_superficie_mare =
                    datiCorrenti.optDouble("sea_surface_temperature", Double.NaN);

            datiMarini.livello_mare_msl =
                    datiCorrenti.optDouble("sea_level_height_msl", Double.NaN);

            datiMarini.direzione_corrente_oceanica =
                    datiCorrenti.optDouble("ocean_current_direction", Double.NaN);

            datiMarini.velocita_corrente_oceanica =
                    datiCorrenti.optDouble("ocean_current_velocity", Double.NaN);

            /* Tipo sorgente dati */
            datiMarini.tipo_sorgente = "API";

            /* Timestamp corrente */
            datiMarini.timestamp = System.currentTimeMillis();

            /* Inserimento nel database */
            databaseLocale.datiMariniDao().insert(datiMarini);
            Log.d("DB", "Dato API completo salvato");
        } catch (Exception errore) {
            Log.e("DB", "Errore salvataggio API", errore);
        }
    }
}