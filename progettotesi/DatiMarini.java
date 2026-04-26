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
    public Long timestamp;
}
