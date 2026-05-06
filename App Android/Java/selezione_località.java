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

import androidx.appcompat.app.AppCompatActivity;

public class selezione_località extends AppCompatActivity {

    private WebView webViewMappa;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!connessioneInternetDisponibile()) {
            mostraMessaggioErrore();
            tornaAlMenu();
            return;
        }

        setContentView(R.layout.mappa);

        inizializzaWebView();
    }

    private void inizializzaWebView() {

        webViewMappa = findViewById(R.id.webViewMappa);

        webViewMappa.getSettings().setJavaScriptEnabled(true);
        webViewMappa.getSettings().setDomStorageEnabled(true);

        /* Collegamento tra codice JavaScript della mappa e applicazione Android */
        webViewMappa.addJavascriptInterface(
                new InterfacciaWebJavaScript(this),
                "AndroidBridge"
        );

        webViewMappa.setWebViewClient(new WebViewClient());

        /* Caricamento della mappa locale per la selezione della posizione */
        webViewMappa.loadUrl("file:///android_asset/index.html");
    }

    private boolean connessioneInternetDisponibile() {

        ConnectivityManager gestoreConnessione =
                (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);

        if (gestoreConnessione == null) return false;

        Network rete = gestoreConnessione.getActiveNetwork();
        if (rete == null) return false;

        NetworkCapabilities capacita =
                gestoreConnessione.getNetworkCapabilities(rete);

        if (capacita == null) return false;

        return capacita.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                && capacita.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);
    }

    private void mostraMessaggioErrore() {
        Toast.makeText(
                this,
                "Connessione Internet non disponibile",
                Toast.LENGTH_LONG
        ).show();
    }

    private void tornaAlMenu() {
        Intent intent = new Intent(this, menu_principale.class);
        startActivity(intent);
        finish();
    }
}