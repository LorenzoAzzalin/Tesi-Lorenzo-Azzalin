package com.example.progettotesi;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.Query;

import java.util.List;

@Dao
public interface DatiMariniDao {

    @Insert
    void insert(DatiMarini dati);

    @Query("SELECT * FROM DatiMarini ORDER BY timestamp DESC")
    List<DatiMarini> getAll();

    @Query("DELETE FROM DatiMarini")
    void deleteAll();
}
