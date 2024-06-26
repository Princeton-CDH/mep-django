/* NOTE: this logic is currently specific to country editing */

// alias jquery to $ for convenience
const $ = jQuery;

$(document).on('select2:select', function(evt) {   // fixme: restrict to .geonames-lookup ?
    var data = evt.params.data;
    // update link display and target
    $('#geonames_uri').text(data.id).attr('href', data.id);
    // set name & code from geonames data
    $('input[name="name"]').val(data.name);
    $('input[name="code"]').val(data.country_code);
});

var map, marker;

function init_map() {
    // initialize the map for the first time
    if ($('#geonames_map').length && typeof L !== "undefined") {
        map = L.map('geonames_map');
        L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
            attribution: '© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>',
            maxZoom: 18,
            id: 'mapbox/streets-v11',
            // get mapbox access token; passed in via hidden form field
            accessToken: $('input[name="mapbox_token"]').val(),
        }).addTo(map);
        // set map to display current coordinates
        update_map();
    }
}

function update_map() {
    var long = $('input[name="longitude"]').val(),
        lat =  $('input[name="latitude"]').val();
    // display map if coordinates are set
    if (lat && long && !(lat == 0.0 && long == 0.0)) {
        $('#geonames_map').show();
        // 5 is good zoom for countries; trying closer default for Paris addresses
        map.setView([lat, long], 15);
        if (typeof marker !== 'undefined') {
            map.removeLayer(marker);
        }
        marker = L.marker([lat, long]).addTo(map);
    } else {        // otherwise, hide it
        $('#geonames_map').hide();
    }
}


$(document).ready(function() {
    if ($('#geonames_map').length) {
       init_map();
    }

    $('input[name="longitude"]').change(function() {
        console.log("longitude changed, updating map");
        update_map(); });
    $('input[name="latitude"]').change(update_map());
});
