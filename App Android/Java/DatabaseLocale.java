package com.example.progettotesi;

import android.content.Context;

import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;

@Database(entities = {DatiMarini.class}, version = 4)
public abstract class DatabaseLocale extends RoomDatabase {

    /* Istanza statica del database utilizzata per implementare il pattern Singleton.
       Questo approccio garantisce che venga creata una sola istanza del database
       durante l'intero ciclo di vita dell'applicazione. */
    private static DatabaseLocale istanzaDatabase;

    public abstract DatiMariniDao datiMariniDao();

    /* Metodo statico sincronizzato che restituisce l'unica istanza del database.
       Se l'istanza non esiste, viene creata; altrimenti viene restituita quella già esistente.
       L'utilizzo del contesto dell'applicazione (getApplicationContext) evita
       memory leak legati al ciclo di vita delle Activity.
       La sincronizzazione garantisce che, in contesti multi-thread, non vengano
       create più istanze contemporaneamente. */
    public static synchronized DatabaseLocale ottieniIstanza(Context contesto) {

        if (istanzaDatabase == null) {

            istanzaDatabase = Room.databaseBuilder(
                            contesto.getApplicationContext(),
                            DatabaseLocale.class,
                            "dati_marini_db"
                    )
                    /* In caso di modifica dello schema senza migrazione definita,
                       il database viene ricreato automaticamente.
                       Questa scelta è accettabile in fase di sviluppo e prototipazione. */
                    .fallbackToDestructiveMigration()

                    /* Permette l'esecuzione di operazioni sul database nel main thread.
                       Sebbene non sia una best practice in applicazioni di produzione,
                       è stata adottata per semplificare la gestione delle operazioni
                       in questa fase del progetto. */
                    .allowMainThreadQueries()
                    .build();
        }

        return istanzaDatabase;
    }
}