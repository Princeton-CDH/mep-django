import { tileLayer, icon } from 'leaflet'
import { TiledMapLayer } from 'esri-leaflet'

// map data - defined in the global scope outside this module, in the template
export type Address = {
    name?: string,
    street_address?: string,
    city: string,
    postal_code?: string,
    arrondissement?: number,
    latitude: number,
    longitude: number,
    start_date?: string,
    end_date?: string,
    member_slugs?: string[]
}

const mapboxAttribution = 'Tiles <a href="https://apps.mapbox.com/feedback/">Mapbox</a>, <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
const PULAttribution = '<a href="https://maps.princeton.edu/catalog/princeton-2r36tz994">Princeton University Library</a>'

export const getMapboxBasemap = (mapboxURL: string , mapboxToken: string) => {
    return tileLayer(`https://api.mapbox.com/styles/v1/mapbox/${mapboxURL}/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`, {
        attribution: mapboxAttribution
    })
}

export const getParisTileLayer = (parisTilesURL: string) => new TiledMapLayer({
    url: parisTilesURL,
    attribution: PULAttribution
})

export const bookstoreIcon = icon({
    iconUrl: '/static/img/icons/bookstore-pin.svg',
    iconSize: [46, 62],
    iconAnchor: [23, 62],
    popupAnchor: [0, -60]
})

export const addressIconInactive = icon({
    iconUrl: '/static/img/icons/inactive-pin.svg',
    iconSize: [46, 70],
    iconAnchor: [23, 70],
    popupAnchor: [0, -70]
})

export const addressIconActive = icon({
    iconUrl: '/static/img/icons/selected-pin.svg',
    iconSize: [46, 70],
    iconAnchor: [23, 70],
    popupAnchor: [0, -70]
})

// generate a paragraph of text from the parts of the address to go in popup
// NOTE not using date information currently, but it should be rendered as:
// <span class="dates">1921-1941</span><p>...</p>
export const popupText = (address: Address) => {
    let text: string = '<p>'
    if (address.name) text += `${address.name}<br/>`
    text += `${address.street_address}<br/>`
    if (address.arrondissement) text += `${address.arrondissement}<br/>`
    else if (address.postal_code) text += `${address.postal_code}<br/>`
    text += `${address.city}</p>`
    return text
}