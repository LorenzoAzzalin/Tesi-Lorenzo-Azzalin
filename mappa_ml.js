document.addEventListener("DOMContentLoaded", function () {

    // CREA LA MAPPA
    var map = L.map('map').setView([0, 0], 2);
    let marker;

    // Rende la variabile accessibile da altri file se serve
    window.map = map;

    // TILE LAYER
    L.tileLayer(`https://api.maptiler.com/maps/ocean/{z}/{x}/{y}.png?key=${CHIAVE_API}`, {
        attribution: '<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a>'
    }).addTo(map);

    // COORDINATE DISPLAY
    L.control.coordinates({
        position: "bottomleft",
        useDMS: true,
        labelTemplateLat: "Lat {y}",
        labelTemplateLng: "Long {x}",
        useLatLngOrder: true
    }).addTo(map);

    // FUNZIONE: elimina marker precedente
    window.eliminaMarker = function (m) {
        if (m) map.removeLayer(m);
    };

    // CLICK SULLA MAPPA
    map.on("click", function (e) {

        eliminaMarker(marker);
        marker = L.marker([e.latlng.lat, e.latlng.lng]).addTo(map);

        let lat = e.latlng.lat;
        let lng = ((e.latlng.lng + 180) % 360 + 360) % 360 - 180;

        console.log("Latitudine:", lat, "\nLongitudine:", lng);

        // LIMITI API
        if (lat > 82 || lat < -82) {
            L.popup()
                .setLatLng([lat, lng])
                .setContent("Area fuori copertura dei dati marini")
                .openOn(map);
            return;
        }

        // CHIAMATA API
        getMarineWeather(lat, lng).then(data => {

            if (!data || !data.hourly) {
                console.error("Dati Open-Meteo non validi");
                return;
            }

            const hourly = data.hourly;

            // Ricaviamo i lag
            const len = hourly.wave_height.length;

            const swh_lag_1 = hourly.wave_height[len - 1];
            const swh_lag_3 = hourly.wave_height[len - 3];

            const mwd = hourly.wave_direction[len - 1];

            const now = new Date();
            const hour = now.getUTCHours();
            const month = now.getUTCMonth() + 1;

            // Placeholder vento (finché non integriamo anche meteo)
            const u10_lag_1 = 5.0;
            const u10_lag_3 = 5.0;
            const v10_lag_1 = 1.0;
            const v10_lag_3 = 1.0;

            const payload = {
                latitude: lat,
                longitude: lng,
                mwd: mwd,
                swh_lag_1: swh_lag_1,
                swh_lag_3: swh_lag_3,
                u10_lag_1: u10_lag_1,
                u10_lag_3: u10_lag_3,
                v10_lag_1: v10_lag_1,
                v10_lag_3: v10_lag_3,
                hour: hour,
                month: month
            };

            console.log("Feature inviate al modello:", payload);

            inviaDatiAlJava(payload);

        });

    });

    // FUNZIONE PER L'API OPEN METEO
    async function getMarineWeather(lat, lon) {

        const baseUrl = 'https://marine-api.open-meteo.com/v1/marine';

        const params = new URLSearchParams({
            latitude: lat,
            longitude: lon,
            hourly: [
                'wave_height',
                'wave_direction'
            ].join(',')
        });

        const url = `${baseUrl}?${params.toString()}`;

        try {

            const resp = await fetch(url);

            if (!resp.ok)
                throw new Error(`Errore HTTP! status: ${resp.status}`);

            const data = await resp.json();

            console.log("Dati Open-Meteo ricevuti");
            console.log(data);

            return data;

        } catch (err) {

            console.error("Errore durante la richiesta Open-Meteo:", err);

        }
    }

});


//Funzione per il passaggio dei dati alla WebView Java
function inviaDatiAlJava(payload) {

    const json = JSON.stringify(payload);

    if (window.AndroidBridge && typeof window.AndroidBridge.riceviCoordinate === "function") {

        AndroidBridge.riceviCoordinate(json);

    } else {

        console.log("AndroidBridge non disponibile, probabilmente sei in browser");

    }

}
