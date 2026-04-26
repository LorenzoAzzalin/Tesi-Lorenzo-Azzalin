package com.example.progettotesi;

import android.os.Bundle;
import android.widget.ArrayAdapter;
import android.widget.ListView;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class mostra_cronologia extends AppCompatActivity {

    private ListView listaCronologia;
    private DatabaseLocale database;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.cronologia);

        inizializzaComponenti();
        inizializzaDatabase();
        mostraDati();
    }

    /* Inizializzazione dei componenti grafici dell'activity */
    private void inizializzaComponenti() {
        listaCronologia = findViewById(R.id.listView);
    }

    /* Inizializzazione del database locale Room tramite Singleton */
    private void inizializzaDatabase() {
        database = DatabaseLocale.ottieniIstanza(getApplicationContext());
    }

    /* Recupero dei dati salvati e popolamento della lista */
    private void mostraDati() {

        List<DatiMarini> risultati = database.datiMariniDao().getAll();

        ArrayList<String> listaStringhe = new ArrayList<>();

        for (DatiMarini d : risultati) {
            listaStringhe.add(costruisciStringaDato(d));
        }

        ArrayAdapter<String> adapter = new ArrayAdapter<>(
                this,
                android.R.layout.simple_list_item_1,
                listaStringhe
        );

        listaCronologia.setAdapter(adapter);
    }

    /* Costruzione della stringa descrittiva per ogni record */
    private String costruisciStringaDato(DatiMarini d) {

        String nomeCorpo = (d.corpo_marino != null && !d.corpo_marino.isEmpty())
                ? d.corpo_marino
                : "N/D";

        return "\n\n" +
                "Corpo marino: " + nomeCorpo +
                "\nData/Ora: " + formattaTimestamp(d.timestamp) +
                "\nLatitudine: " + formattaCoordinata(d.latitudine) + " °" +
                "\nLongitudine: " + formattaCoordinata(d.longitudine) + " °" +
                "\nAltezza onda: " + formattaValore(d.altezza_onda, "m") +
                "\nDirezione onda: " + formattaValore(d.direzione_onda, "°") +
                "\nAltezza vento-onde: " + formattaValore(d.altezza_onda_vento, "m") +
                "\nDirezione vento-onde: " + formattaValore(d.direzione_onda_vento, "°") +
                "\nPeriodo vento-onde: " + formattaValore(d.periodo_onda_vento, "s") +
                "\nTemperatura superficie mare: " + formattaValore(d.temperatura_superficie_mare, "°C") +
                "\nLivello mare (MSL): " + formattaValore(d.livello_mare_msl, "m") +
                "\nDirezione corrente: " + formattaValore(d.direzione_corrente_oceanica, "°") +
                "\nVelocità corrente: " + formattaValore(d.velocita_corrente_oceanica, "m/s") +
                "\n";
    }

    /* Funzione per gestire il numero di decimali nelle coordinate */
    private String formattaCoordinata(Double valore) {
        if (valore == null) return "N/D";
        return String.format(Locale.getDefault(), "%.4f", valore);
    }

    /* Funzione che converte il timestamp in una data leggibile */
    private String formattaTimestamp(Long timestamp) {
        if (timestamp == null) return "N/D";

        SimpleDateFormat sdf =
                new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault());

        return sdf.format(new Date(timestamp));
    }

    /* Funzione che gestisce valori null e aggiunge l'unità di misura */
    private String formattaValore(Double valore, String unita) {
        return valore != null ? valore + " " + unita : "N/D";
    }
}