document.addEventListener("DOMContentLoaded", function () {
    // Crea la mappa iniziale centrata sul globo
    const mappa = L.map('map').setView([0, 0], 2);
    // Variabile che contiene il marcatore corrente
    let marcatore;
    // Rende la mappa accessibile anche da altri file
    window.mappa = mappa;
    // Aggiunge il layer grafico marino
    L.tileLayer(`https://api.maptiler.com/maps/ocean/{z}/{x}/{y}.png?key=${CHIAVE_API}`, {
        attribution:'<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a>'}).addTo(mappa);

    // Aggiunge il controllo coordinate
    L.control.coordinates({
        position: "bottomleft",
        useDMS: true,
        labelTemplateLat: "Lat {y}",
        labelTemplateLng: "Long {x}",
        useLatLngOrder: true
    }).addTo(mappa);

    // Funzione che elimina un marcatore dalla mappa
    window.eliminaMarcatore = function (marcatoreDaEliminare) {
        if (marcatoreDaEliminare) {
            mappa.removeLayer(marcatoreDaEliminare);
        }
    };

    // Gestisce il click dell'utente sulla mappa
    mappa.on("click", function (evento) {
        // Elimina il marcatore precedente
        eliminaMarcatore(marcatore);
        // Inserisce un nuovo marcatore
        marcatore = L.marker([
            evento.latlng.lat,
            evento.latlng.lng
        ]).addTo(mappa);

        // Recupera le coordinate selezionate
        const latitudine = evento.latlng.lat;
        const longitudine = ((evento.latlng.lng + 180) % 360 + 360) % 360 - 180;
        console.log("Latitudine:", latitudine);
        console.log("Longitudine:", longitudine);

        // Controlla che il punto rientri nei limiti API
        if (latitudine > 82 || latitudine < -82) {

            L.popup()
                .setLatLng([latitudine, longitudine])
                .setContent("Area fuori copertura dei dati marini")
                .openOn(mappa);
            return;
        }

        // Richiede i dati meteo-marini
        ottieniDatiMeteoMarini(latitudine, longitudine).then(dati => {
            // Controlla che siano presenti dati validi
            if (!dati || !dati.current || dati.current.sea_surface_temperature === null) {
                L.popup()
                    .setLatLng([latitudine, longitudine])
                    .setContent(
                        "Seleziona una superficie marittima"
                    )
                    .openOn(mappa);
                return;
            }

            // Recupera il nome del corpo marino
            ottieniNomeCorpoMarinoGeoNames(latitudine, longitudine,'l.azzalin')
            .then(nomeCorpoMarino => {
                const datiCorrenti = dati.current;
                // Funzione che formatta i valori null
                const formattaDato = valore => {
                    return valore == null
                        ? "dato non disponibile"
                        : valore;
                };

                // Costruisce il contenuto HTML del popup
                const contenutoPopup = `
                    <b>Dati Meteo-Marini Attuali</b><br><br>
                    <b>Geolocalizzazione</b>:
                    ${nomeCorpoMarino}<br><br>
                    <b>Altezza onda</b>:
                    ${formattaDato(datiCorrenti.wave_height)} m<br>
                    <b>Direzione onda</b>:
                    ${formattaDato(datiCorrenti.wave_direction)}°<br><br>
                    <b>Direzione onde da vento</b>:
                    ${formattaDato(datiCorrenti.wind_wave_direction)}°<br>
                    <b>Periodo onde da vento</b>:
                    ${formattaDato(datiCorrenti.wind_wave_period)} s<br><br>
                    <b>Temperatura superficie mare</b>:
                    ${formattaDato(datiCorrenti.sea_surface_temperature)} °C<br>
                    <b>Livello medio del mare</b>:
                    ${formattaDato(datiCorrenti.sea_level_height_msl)} m<br><br>
                    <b>Direzione corrente oceanica</b>:
                    ${formattaDato(datiCorrenti.ocean_current_direction)}°<br>
                    <b>Velocità corrente oceanica</b>:
                    ${formattaDato(datiCorrenti.ocean_current_velocity)} m/s<br>
                `;

                // Mostra il popup sulla mappa
                L.popup()
                    .setLatLng([latitudine, longitudine])
                    .setContent(contenutoPopup)
                    .openOn(mappa);

                // Invia i dati alla WebView Android
                inviaDatiAllaWebView(latitudine, longitudine, dati, nomeCorpoMarino);
            })
            .catch(errore => {
                console.error(errore);
            });
        });
    });

    // Funzione che richiede dati meteo-marini
    async function ottieniDatiMeteoMarini(latitudine, longitudine) {

      const urlBase = 'https://marine-api.open-meteo.com/v1/marine';

        // Parametri della richiesta API
        const parametriRichiesta =
            new URLSearchParams({
                latitude: latitudine,
                longitude: longitudine,

                hourly: [
                    'wave_height',
                    'wave_direction',
                    'wave_period',
                    'wave_peak_period',
                    'wind_wave_height',
                    'wind_wave_direction',
                    'swell_wave_height',
                    'swell_wave_direction'
                ].join(','),

                current: [
                    'wave_height',
                    'wave_direction',
                    'wind_wave_height',
                    'wind_wave_direction',
                    'wind_wave_period',
                    'sea_surface_temperature',
                    'sea_level_height_msl',
                    'ocean_current_direction',
                    'ocean_current_velocity'
                ].join(',')
            });

        const url = `${urlBase}?${parametriRichiesta.toString()}`;

        try {
            const risposta = await fetch(url);
            if (!risposta.ok) {
                throw new Error(`Errore HTTP: ${risposta.status}`);
            }
            const dati = await risposta.json();
            console.log("Dati meteo-marini ricevuti");
            console.log(dati);
            return dati;
        } catch (errore) {
            console.error("Errore richiesta Open-Meteo:",errore);
        }
    }
});

// Funzione che invia i dati alla WebView Android
function inviaDatiAllaWebView(latitudine, longitudine, datiMeteo, nomeLocalita) {

    // Aggiunge il nome della località ai dati
    const datiConLocalita = {
        ...datiMeteo,
        localita: nomeLocalita || null
    };

    // Converte i dati in formato JSON
    const jsonMeteo = JSON.stringify(datiConLocalita);

    // Verifica se AndroidBridge è disponibile
    if (window.AndroidBridge && typeof window.AndroidBridge.riceviDati === "function") {
        AndroidBridge.riceviDati(latitudine.toString(), longitudine.toString(),jsonMeteo);
    } else {
        console.log("AndroidBridge non disponibile");
    }
}

// Funzione che recupera il nome del corpo marino
async function ottieniNomeCorpoMarinoGeoNames(latitudine,longitudine, nomeUtente) {

    const url =
        `https://secure.geonames.org/oceanJSON?lat=${latitudine}&lng=${longitudine}&username=${nomeUtente}`;
    try {
        const risposta = await fetch(url);
        if (!risposta.ok) {
            throw new Error(
                "Errore richiesta GeoNames"
            );
        }

        const dati = await risposta.json();

        console.log("Risposta GeoNames:");
        console.log(dati);

        // Verifica se il nome dell'oceano è disponibile
        if (dati.ocean && dati.ocean.name) {
            return dati.ocean.name;
        } else {
            return null;
        }
    } catch (errore) {
        console.error(errore);
        return null;
    }
}
