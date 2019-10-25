import { map, latLng, latLngBounds, icon, marker } from 'leaflet'
import { TiledMapLayer } from 'esri-leaflet'

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
    popupAnchor: [23, 0]
})

const bookstoreMarker = marker([48.85089, 2.338502], { icon: bookstoreIcon })

parisTiles.addTo(addressMap)

bookstoreMarker.addTo(addressMap)

addressMap.setView([48.85089, 2.338502], 14)

addressMap.setMaxBounds(latLngBounds(
    latLng(48.906619, 2.243891),
    latLng(48.810564, 2.422762)
))
