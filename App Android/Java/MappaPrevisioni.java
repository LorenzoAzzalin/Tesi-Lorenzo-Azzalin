package com.example.progettotesi;

import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Bundle;
import android.widget.Toast;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.widget.AdapterView;
import android.view.View;

import androidx.appcompat.app.AppCompatActivity;

public class MappaPrevisioni extends AppCompatActivity {

    private WebView webViewMappa;
    private InterfacciaWebJavaScript bridge;

    /* Variabile globale per l'orizzonte selezionato */
    public static int ORIZZONTE = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Controllo se l'utente ha connessione internet
        if (!connessioneInternetDisponibile()) {
            Toast.makeText(this,
                    "Connessione Internet non disponibile",
                    Toast.LENGTH_LONG).show();

            Intent intent = new Intent(this, menu_principale.class);
            startActivity(intent);
            finish();
            return;
        }

        // Layout della mappa per il modello ML
        setContentView(R.layout.mappa_ml);
        webViewMappa = findViewById(R.id.webViewMappaML);
        webViewMappa.getSettings().setJavaScriptEnabled(true);
        webViewMappa.getSettings().setDomStorageEnabled(true);

        // Bridge tra JavaScript e Android
        bridge = new InterfacciaWebJavaScript(this);
        webViewMappa.addJavascriptInterface(
                bridge,
                "AndroidBridge"
        );

        webViewMappa.setWebViewClient(new WebViewClient());

        // Carica la pagina della mappa dedicata al modello ML
        webViewMappa.loadUrl("file:///android_asset/index_ml.html");

        /* Spinner per selezione orizzonte (preso dal layout XML) */
        Spinner spinner = findViewById(R.id.selettoreOrizzonte);

        String[] opzioni = {"1", "6", "12", "24"};

        ArrayAdapter<String> adapter =
                new ArrayAdapter<>(
                        this,
                        android.R.layout.simple_spinner_dropdown_item,
                        opzioni
                );
        spinner.setAdapter(adapter);
        spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                ORIZZONTE = Integer.parseInt(opzioni[position]);
                /* Aggiornamento dinamico JS */
                webViewMappa.evaluateJavascript(
                        "window.HORIZON_ANDROID = " + ORIZZONTE,
                        null
                );
            }
            @Override
            public void onNothingSelected(AdapterView<?> parent) {}
        });

        /* Imposta valore iniziale dell'orizzonte nel JS */
        webViewMappa.postDelayed(() -> {
            String js = "window.HORIZON_ANDROID = " + ORIZZONTE + ";";
            webViewMappa.evaluateJavascript(js, null);

        }, 1000);
    }

    private boolean connessioneInternetDisponibile() {
        ConnectivityManager gestoreConnessione =
                (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);

        if (gestoreConnessione == null) return false;

        Network rete = gestoreConnessione.getActiveNetwork();
        if (rete == null) return false;

        NetworkCapabilities capacita = gestoreConnessione.getNetworkCapabilities(rete);

        if (capacita == null) return false;

        return capacita.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                && capacita.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);
    }
}