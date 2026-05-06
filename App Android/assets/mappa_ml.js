document.addEventListener("DOMContentLoaded", function () {

    // Variabile di sicurezza per evitare richieste multiple simultanee
    let richiestaInCorso = false;

    // Crea la mappa iniziale centrata sul globo
    const mappa = L.map('map').setView([0, 0], 2);

    // Variabile che contiene il marcatore corrente
    let marcatore;

    // Aggiunge il layer grafico marino alla mappa
    L.tileLayer(`https://api.maptiler.com/maps/ocean/{z}/{x}/{y}.png?key=${CHIAVE_API}`, {
        attribution: '&copy; MapTiler'
    }).addTo(mappa);

    // Gestisce il click dell'utente sulla mappa
    mappa.on("click", function (evento) {

        // Blocca nuovi click se una richiesta è già in corso
        if (richiestaInCorso) {
            console.log("Richiesta già in corso");
            return;
        }

        richiestaInCorso = true;

        // Rimuove il marcatore precedente
        if (marcatore) {
            mappa.removeLayer(marcatore);
        }

        // Inserisce il nuovo marcatore
        marcatore = L.marker([
            evento.latlng.lat,
            evento.latlng.lng
        ]).addTo(mappa);

        // Recupera le coordinate selezionate
        const latitudine = evento.latlng.lat;

        // Normalizza la longitudine nell'intervallo [-180, 180]
        const longitudine =
            ((evento.latlng.lng + 180) % 360 + 360) % 360 - 180;

        // Richiede i dati marini all'API Open-Meteo
        ottieniDatiMarini(latitudine, longitudine)
            .then(dati => {
                // Verifica che i dati esistano
                if (!dati || !dati.hourly) {
                    richiestaInCorso = false;
                    return;
                }

                // Recupera i dati orari
                const datiOrari = dati.hourly;
                // Numero totale di valori disponibili
                const numeroValori = datiOrari.wave_height.length;

                // Recupera l'ultimo valore disponibile
                const altezzaOnde = datiOrari.wave_height[numeroValori - 1];
                const direzioneOnde = datiOrari.wave_direction[numeroValori - 1];

                // Recupera data e ora UTC correnti
                const dataCorrente = new Date();
                const oraCorrente = dataCorrente.getUTCHours();
                const meseCorrente = dataCorrente.getUTCMonth() + 1;

                // Converte la direzione delle onde in radianti
                const direzioneOndeRadianti =
                    direzioneOnde * Math.PI / 180;

                // Costruisce il payload per il modello ML
                const datiModelloML = {
                    latitude: latitudine,
                    longitude: longitudine,
                    swh: altezzaOnde,
                    mwd_sin: Math.sin(direzioneOndeRadianti),
                    mwd_cos: Math.cos(direzioneOndeRadianti),
                    hour_sin:
                        Math.sin(2 * Math.PI * oraCorrente / 24),
                    hour_cos:
                        Math.cos(2 * Math.PI * oraCorrente / 24),

                    month_sin:
                        Math.sin(2 * Math.PI * meseCorrente / 12),
                    month_cos:
                        Math.cos(2 * Math.PI * meseCorrente / 12)
                };
                console.log("Payload modello ML:");
                console.log(datiModelloML);
                // Invia i dati alla WebView Android
                inviaDatiAllaWebView(datiModelloML);
                // Sblocco automatico di sicurezza
                setTimeout(() => {
                    richiestaInCorso = false;
                    console.log("Richiesta sbloccata automaticamente");
                }, 5000);
            })
            .catch(errore => {
                console.error(errore);
                richiestaInCorso = false;
            });
    });

    // Funzione che richiede i dati marini all'API
    async function ottieniDatiMarini(latitudine, longitudine) {
        const url =
            `https://marine-api.open-meteo.com/v1/marine?latitude=${latitudine}&longitude=${longitudine}&hourly=wave_height,wave_direction`;
        try {
            const risposta = await fetch(url);
            return await risposta.json();
        } catch (errore) {
            console.error(errore);
            richiestaInCorso = false;

        }
    }
});

// Funzione che invia i dati alla WebView Android
function inviaDatiAllaWebView(datiModelloML) {
    // Converte i dati in formato JSON
    const jsonDati = JSON.stringify(datiModelloML);
    // Verifica se la WebView Android è disponibile
    if (window.AndroidBridge) {
        AndroidBridge.riceviCoordinate(jsonDati);
    } else {
        console.log("AndroidBridge non disponibile");

    }
}
