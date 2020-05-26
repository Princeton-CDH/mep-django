import { map, Map, control, marker, Marker, featureGroup, PopupEvent, latLngBounds } from 'leaflet'
import { Address, getMapboxBasemap, getParisTileLayer, bookstoreIcon, addressIconActive, addressIconInactive, popupText } from '../lib/map'

import addressData from '../lib/map-data'

declare const mapboxToken: string
declare const mapboxBasemap: string
declare const parisOverlay: string

export default class MemberSearchMap {

    private readonly ADDRESS_DATA_URL: '/foo'

    private map: Map
    private bookstoreMarker: Marker
    private addressMarkers: Marker[]
    
    constructor($container: HTMLDivElement) {
        // create map
        this.map = map($container, { zoomControl: false })
        control.zoom({ position: 'bottomright' }).addTo(this.map)

        // add basemap & paris overlay
        getMapboxBasemap(mapboxBasemap, mapboxToken).addTo(this.map)
        getParisTileLayer(parisOverlay).addTo(this.map)

        // add all active address markers & zoom map to fit
        this.update()

        // add library marker
        const libraryAddressDataElement = document.getElementById('library-address') as HTMLElement
        const libraryAddress = JSON.parse(libraryAddressDataElement.textContent || '') as Address|null
        if (libraryAddress) {
            this.bookstoreMarker = marker([libraryAddress.latitude, libraryAddress.longitude], {
                icon: bookstoreIcon,
                zIndexOffset: 1000, // on top of address markers
            })
            this.bookstoreMarker.bindPopup(popupText(libraryAddress))
            this.bookstoreMarker.addTo(this.map)
        }

        this.map.fitBounds(latLngBounds([this.bookstoreMarker.getLatLng()]).pad(0.4))
    }

    update() {
        // TODO hit the URL for data
        const { addresses, members } = addressData

        this.addressMarkers = addresses.map((address: Address) => {
            return marker(
                [address.latitude,address.longitude],
                { icon: addressIconInactive }
            ).bindPopup(popupText(address))
        })

        this.addressMarkers
            .map(m => m.on('popupopen', this.onPopupOpen))
            .map(m => m.on('popupclose', this.onPopupClose))
            .map(m => m.addTo(this.map))
    }

    private onPopupOpen(event: PopupEvent) {
        event.target.setIcon(addressIconActive)
    }

    private onPopupClose(event: PopupEvent) {
        event.target.setIcon(addressIconInactive)
    }

    private sidebarContent(address: Address) {
        
    }
}