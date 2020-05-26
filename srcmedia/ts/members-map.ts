import { map, marker, control, featureGroup, PopupEvent } from 'leaflet'

import { Address, getMapboxBasemap, getParisTileLayer, bookstoreIcon, addressIconActive, addressIconInactive, popupText } from './lib/map'

const addressDataElement = document.getElementById('address-data') as HTMLElement
const addressData = JSON.parse(addressDataElement.textContent || '') as Array<Address>

const libraryAddressDataElement = document.getElementById('library-address') as HTMLElement
const libraryAddress = JSON.parse(libraryAddressDataElement.textContent || '') as Address|null

// defined in local_settings.py and passed in the django view/template
declare const mapboxToken: string
declare const mapboxBasemap: string
declare const parisOverlay: string

// map object with custom zoom control in bottom right
const target = document.getElementById('address-map') as HTMLDivElement
const addressMap = map(target, { zoomControl: false })
const zoomControl = control.zoom({ position: 'bottomright' })
zoomControl.addTo(addressMap)

// simple global basemap from mapbox
getMapboxBasemap(mapboxBasemap, mapboxToken).addTo(addressMap)

// historic map of paris overlay
getParisTileLayer(parisOverlay).addTo(addressMap)

// bookstore icon + marker on map
let bookstoreMarker

if (libraryAddress) { // only add if data is available

    bookstoreMarker = marker([libraryAddress.latitude, libraryAddress.longitude], {
        icon: bookstoreIcon,
        zIndexOffset: 1, // on top of address markers
    })

    bookstoreMarker.bindPopup(popupText(libraryAddress))
    bookstoreMarker.addTo(addressMap)
}

// handlers that switch the icon when popup is active
function onPopupOpen (event: PopupEvent) {
    event.target.setIcon(addressIconActive)
}

function onPopupClose (event: PopupEvent) {
    event.target.setIcon(addressIconInactive)
}

// create the actual markers
const addressMarkers = addressData.map(a => {
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

// zoom to fit all markers
const allMarkers = featureGroup([...addressMarkers])
if (bookstoreMarker) allMarkers.addLayer(bookstoreMarker)

addressMap.fitBounds(allMarkers.getBounds().pad(0.1))

// open the first marker: needs a delay otherwise the text inside will be
// truncated, leaflet bug?
setTimeout(() => addressMarkers[0].openPopup(), 100)
