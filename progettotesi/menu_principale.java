package com.example.progettotesi;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class menu_principale extends AppCompatActivity {

    private Button bottoneMappa;
    private Button bottoneCronologia;
    private Button bottoneCancellaCronologia;
    private Button bottonePrevisioneAI;

    private DatabaseLocale database;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.menu_principale);

        inizializzaDatabase();
        inizializzaComponenti();
        impostaListener();
    }

    /* Inizializzazione del database tramite Singleton */
    private void inizializzaDatabase() {
        database = DatabaseLocale.ottieniIstanza(this);
    }

    private void inizializzaComponenti() {
        bottoneMappa = findViewById(R.id.btnMappa);
        bottoneCronologia = findViewById(R.id.btnCronologia);
        bottoneCancellaCronologia = findViewById(R.id.btnCancellaCronologia);
        bottonePrevisioneAI = findViewById(R.id.btnPrevisioneAI);
    }

    private void impostaListener() {

        /* Apertura mappa per selezione posizione marina */
        bottoneMappa.setOnClickListener(v -> {
            startActivity(new Intent(this, selezione_località.class));
        });

        /* Apertura schermata cronologia dati salvati */
        bottoneCronologia.setOnClickListener(v -> {
            startActivity(new Intent(this, mostra_cronologia.class));
        });

        /* Eliminazione di tutti i dati salvati */
        bottoneCancellaCronologia.setOnClickListener(v -> {
            database.datiMariniDao().deleteAll();
            Toast.makeText(this, "Cronologia eliminata", Toast.LENGTH_SHORT).show();
        });

        /* Apertura schermata previsione ML */
        bottonePrevisioneAI.setOnClickListener(v -> {
            startActivity(new Intent(this, MappaPrevisioni.class));
        });
    }
}