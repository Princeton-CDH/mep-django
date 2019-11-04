import { map, latLng, latLngBounds, icon, marker } from 'leaflet'
import { TiledMapLayer } from 'esri-leaflet'

// defined in the global scope outside this module, in the template
type Address = {
    name: string,
    street_address: string,
    city: string,
    postal_code: number,
    latitude: number,
    longitude: number,
    start_date: string,
    end_date: string,
    care_of_person: string
}
declare const address_data: Array<Address>

const target = document.getElementById('address-map') as HTMLDivElement
const addressMap = map(target)

const parisTiles = new TiledMapLayer({
    url: 'https://tiles.arcgis.com/tiles/4Ko8f1mCWFLyY4NV/arcgis/rest/services/Paris_1943/MapServer',
    attribution: 'Map <a href="https://maps.princeton.edu/catalog/princeton-2r36tz994">Princeton University Library</a>',
    maxZoom: 18,
    minZoom: 13,
})

const bookstoreIcon = icon({
    iconUrl: '/static/img/icons/bookstore-pin.svg',
    iconSize: [46, 62],
    iconAnchor: [23, 62],
    popupAnchor: [0, -60]
})

const addressIcon = icon({
    iconUrl: '/static/img/icons/inactive-pin.svg',
    iconSize: [46, 70],
    iconAnchor: [23, 70],
    popupAnchor: [0, -70]
})

const bookstoreMarker = marker([48.85089, 2.338502], { icon: bookstoreIcon })
    .bindPopup(`<p>
        Shakespeare and Company<br/>
        12 rue de l’Odéon<br/>
        Paris<br/>
    </p>`)

function popupText ({ name, street_address, city, postal_code }: Address): string {
    const parts = [name, street_address, postal_code, city].filter(p => !!p)
    return `<p>${parts.join('<br/>')}</p>`
}

const addressMarkers = address_data.map(a => {
    return marker([a.latitude, a.longitude], { icon: addressIcon })
        .bindPopup(popupText(a))
})

parisTiles.addTo(addressMap)

bookstoreMarker.addTo(addressMap)

addressMarkers.forEach(m => m.addTo(addressMap))

addressMarkers

addressMap.setView([48.85089, 2.338502], 13)

addressMap.setMaxBounds(latLngBounds(
    latLng(48.906619, 2.243891),
    latLng(48.810564, 2.422762)
))


