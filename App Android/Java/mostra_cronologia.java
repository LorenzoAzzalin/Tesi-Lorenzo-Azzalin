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
        listaCronologia = findViewById(R.id.listaCronologia);
    }

    /* Inizializzazione del database locale Room tramite Singleton */
    private void inizializzaDatabase() {
        database = DatabaseLocale.ottieniIstanza(getApplicationContext());
    }

    /* Recupero dei dati salvati e popolamento della lista */
    private void mostraDati() {

        List<DatiMarini> risultati = database.datiMariniDao().getAll();
        ArrayList<String> listaStringhe = new ArrayList<>();

        for (DatiMarini dato : risultati) {
            listaStringhe.add(costruisciStringaDato(dato));
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
        // Stringa contenente le informazioni prese dal database e stampata sull'UI
        String base =
                "\n" +
                        "Fonte informazione: " + (d.tipo_sorgente != null ? d.tipo_sorgente : "API") +
                        "\nData/Ora: " + formattaTimestamp(d.timestamp) +
                        "\n\nPosizione" +
                        "\nLatitudine: " + formattaCoordinata(d.latitudine) + " °" +
                        "\nLongitudine: " + formattaCoordinata(d.longitudine) + " °";

        if ("API".equals(d.tipo_sorgente)) {
            String nomeCorpo = (d.corpo_marino != null && !d.corpo_marino.isEmpty())
                    ? d.corpo_marino
                    : "N/D";
            base += "\nCorpo marino: " + nomeCorpo;
        }

        // Dati forniti dall'API
        if ("API".equals(d.tipo_sorgente)) {

            base +=
                    "\n\nOnde" +
                            "\nAltezza: " + formattaValore(d.altezza_onda, "m") +
                            "\nDirezione: " + formattaValore(d.direzione_onda, "°") +

                            "\n\nOnde da vento" +
                            "\nAltezza: " + formattaValore(d.altezza_onda_vento, "m") +
                            "\nDirezione: " + formattaValore(d.direzione_onda_vento, "°") +
                            "\nPeriodo: " + formattaValore(d.periodo_onda_vento, "s") +

                            "\n\nMare" +
                            "\nTemperatura: " + formattaValore(d.temperatura_superficie_mare, "°C") +
                            "\nLivello (MSL): " + formattaValore(d.livello_mare_msl, "m") +

                            "\n\nCorrenti" +
                            "\nDirezione: " + formattaValore(d.direzione_corrente_oceanica, "°") +
                            "\nVelocità: " + formattaValore(d.velocita_corrente_oceanica, "m/s") + "\n\n";
        }

        // Dati ML previsti dal modello
        if ("ML".equals(d.tipo_sorgente)) {

            base +=
                    "\n\nOnde" +
                            "\nAltezza: " + formattaValore(d.altezza_onda, "m") +
                            "\n\nMare" +
                            "\nTemperatura: " + formattaValore(d.temperatura_superficie_mare, "°C") +
                            "\nPressione: " + formattaValore(d.livello_mare_msl, "hPa") +

                            "\n\nVento" +
                            "\nu10: " + formattaValore(d.u10, "m/s") +
                            "\nv10: " + formattaValore(d.v10, "m/s") + "\n\n";
        }

        return base;
    }

    /* Funzione per gestire il numero di decimali nelle coordinate */
    private String formattaCoordinata(Double valore) {
        if (valore == null) return "N/D";
        return String.format(Locale.getDefault(), "%.4f", valore);
    }

    /* Funzione che converte il timestamp in una data leggibile */
    private String formattaTimestamp(Long timestamp) {
        if (timestamp == null) return "N/D";

        SimpleDateFormat formato_sempl =
                new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault());

        return formato_sempl.format(new Date(timestamp));
    }

    /* Funzione che gestisce valori null e aggiunge l'unità di misura */
    private String formattaValore(Double valore, String unita) {
        if (valore == null) return "N/D";
        return String.format(Locale.getDefault(), "%.2f", valore) + " " + unita;
    }
}