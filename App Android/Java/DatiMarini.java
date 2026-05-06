package com.example.progettotesi;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity
public class DatiMarini {

    /* Qui vengono dichiarate tutte le variabili che verranno fornite in risposta dall'API */
    @PrimaryKey(autoGenerate = true)
    public int id;

    public String corpo_marino;
    public Double latitudine;
    public Double longitudine;

    public Double altezza_onda;
    public Double direzione_onda;
    public Double altezza_onda_vento;
    public Double direzione_onda_vento;
    public Double periodo_onda_vento;
    public Double temperatura_superficie_mare;
    public Double livello_mare_msl;
    public Double direzione_corrente_oceanica;
    public Double velocita_corrente_oceanica;

    /* Variabili aggiunte per il modello di Machine Learning */
    public Double u10;
    public Double v10;
    public Double t2m;
    public Double tp_hourly;
    public Double pp1d;

    /* Campo per distinguere la sorgente del dato:
       "API" = dati della chiamata all'api
       "ML" = dati predetti dal modello */
    public String tipo_sorgente;

    public Long timestamp;
}