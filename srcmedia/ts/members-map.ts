import { map, icon, marker, tileLayer, control, featureGroup, PopupEvent } from 'leaflet'
import { TiledMapLayer } from 'esri-leaflet'

// map data - defined in the global scope outside this module, in the template
type Address = {
    name: string,
    street_address: string,
    city: string,
    postal_code: number,
    latitude: number,
    longitude: number,
    start_date: string,
    end_date: string,
}

declare const address_data: Array<Address>

/*
 * map object with custom zoom control in bottom right
 */
const target = document.getElementById('address-map') as HTMLDivElement
const addressMap = map(target, { zoomControl: false })
const zoomControl = control.zoom({ position: 'bottomright' })

zoomControl.addTo(addressMap)

/*
* basic tiled basemap from mapbox
*/
const mapboxToken = 'pk.eyJ1IjoicHJpbmNldG9uLWNkaCIsImEiOiJjazJrd2lybnEwMHdsM2JvM3UyMHUwbm02In0.4GJpwErZHkJH1DU-E-72OA'
const basemap = tileLayer(`https://api.mapbox.com/styles/v1/mapbox/light-v10/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`, {
    attribution: 'Tiles <a href="https://apps.mapbox.com/feedback/">Mapbox</a>, <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
})

basemap.addTo(addressMap)

/*
 * historic map of paris overlay
 */
const parisTiles = new TiledMapLayer({
    url: 'https://tiles.arcgis.com/tiles/4Ko8f1mCWFLyY4NV/arcgis/rest/services/Paris_1943/MapServer',
    attribution: '<a href="https://maps.princeton.edu/catalog/princeton-2r36tz994">Princeton University Library</a>',
})

parisTiles.addTo(addressMap)

/*
 * bookstore icon + marker on map
 */
const bookstoreIcon = icon({
    iconUrl: '/static/img/icons/bookstore-pin.svg',
    iconSize: [46, 62],
    iconAnchor: [23, 62],
    popupAnchor: [0, -60]
})

const bookstoreMarker = marker([48.85089, 2.338502], { icon: bookstoreIcon })
    .bindPopup(`
    <span class="dates">1921-1941</span>
    <p>
        Shakespeare and Company<br/>
        12 rue de l’Odéon<br/>
        Paris<br/>
    </p>`)

bookstoreMarker.addTo(addressMap)

/*
 * address icons + markers on map
 */
const addressIconInactive = icon({
    iconUrl: '/static/img/icons/inactive-pin.svg',
    iconSize: [46, 70],
    iconAnchor: [23, 70],
    popupAnchor: [0, -70]
})

const addressIconActive = icon({
    iconUrl: '/static/img/icons/selected-pin.svg',
    iconSize: [46, 70],
    iconAnchor: [23, 70],
    popupAnchor: [0, -70]
})

// generate a paragraph of text from the parts of the address to go in popup
// NOTE not using date information currently, but it should be rendered as:
// <span class="dates">1921-1941</span><p>...</p>
function popupText ({ name, street_address, city, postal_code }: Address): string {
    const parts = [name, street_address, postal_code, city].filter(p => !!p)
    return `<p>${parts.join('<br/>')}</p>`
}

// handlers that switch the icon when popup is active
function onPopupOpen (event: PopupEvent) {
    event.target.setIcon(addressIconActive)
}

function onPopupClose (event: PopupEvent) {
    event.target.setIcon(addressIconInactive)
}

// create the actual markers
const addressMarkers = address_data.map(a => {
    return marker([a.latitude, a.longitude], { icon: addressIconInactive })
        .bindPopup(popupText(a))
})

// bind handlers and add to map
addressMarkers
    .map(m => m.on('popupopen', onPopupOpen))
    .map(m => m.on('popupclose', onPopupClose))
    .map(m => m.addTo(addressMap))

/*
 * set up initial zoom/view
 */
const allMarkers = featureGroup([bookstoreMarker, ...addressMarkers])
addressMap.fitBounds(allMarkers.getBounds().pad(0.1))
addressMarkers[0].openPopup()
