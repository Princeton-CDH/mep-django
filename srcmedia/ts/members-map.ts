import { map } from 'leaflet'
import { TiledMapLayer } from 'esri-leaflet'

const target = document.getElementById('address-map') as HTMLDivElement
const addressMap = map(target)

const parisTiles = new TiledMapLayer({
    url: 'https://tiles.arcgis.com/tiles/4Ko8f1mCWFLyY4NV/arcgis/rest/services/Paris_1943/MapServer',
    attribution: 'Map <a href="https://maps.princeton.edu/catalog/princeton-2r36tz994">Princeton University Library</a>',
    maxZoom: 19,
})

parisTiles.addTo(addressMap)

addressMap.setView([48.8589101, 2.3120407], 14)
