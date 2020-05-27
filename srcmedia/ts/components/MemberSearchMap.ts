import { map, Map, control, marker, Marker, featureGroup, PopupEvent, markerClusterGroup, MarkerClusterGroup } from 'leaflet'
import 'leaflet.markercluster'

import { Address, getMapboxBasemap, getParisTileLayer, bookstoreIcon, addressIconActive, addressIconInactive, popupText } from '../lib/map'
import { ajax } from '../lib/common'

declare const mapboxToken: string
declare const mapboxBasemap: string
declare const parisOverlay: string

type Member = {
    slug: string,
    has_card: boolean,
    sort_name: string[],
    account_years: string
}

type AddressSolrResults = {
    numFound: {
        addresses: number,
        members: number,
    },
    addresses: Address[],
    members: {
        [slug: string]: Member
    }
}

export default class MemberSearchMap {

    private readonly ENDPOINT = '/accounts/addresses/'

    private map: Map
    private library: Address
    private libraryMarker: Marker
    private addressMarkers: MarkerClusterGroup

    // TODO
    /*
    - make group circles monochrome/match marker icon
    - display member names with markers when markers are shown
    */
    
    constructor($container: HTMLDivElement) {
        // parse the library's address from a data element
        const libraryAddressDataElement = document.getElementById('library-address') as HTMLElement
        this.library = JSON.parse(libraryAddressDataElement.textContent as string) as Address

        // create map centered on library
        this.map = map($container, {
            zoomControl: false,
            center: [this.library.latitude, this.library.longitude],
            zoom: 14,
            layers: [
                getMapboxBasemap(mapboxBasemap, mapboxToken),
                getParisTileLayer(parisOverlay)
            ]
        })

        control.zoom({ position: 'bottomright' }).addTo(this.map)
        this.map.scrollWheelZoom.disable()

        // add all active address markers
        this.addressMarkers = markerClusterGroup({
            showCoverageOnHover: false,
            maxClusterRadius: 40,
        })
        this.map.addLayer(this.addressMarkers)
        this.update()

        // add library marker on top of address markers
        this.libraryMarker = marker([this.library.latitude, this.library.longitude], {
            icon: bookstoreIcon,
            zIndexOffset: 1000,
        })
        .bindPopup(popupText(this.library))
        .addTo(this.map)
    }

    async update() {
        return fetch(location.origin + this.ENDPOINT, ajax)
            .then(response => response.json())
            .then((data: AddressSolrResults) => {
                const addressMarkers = data.addresses.map(address => {
                    const addressMarker = marker(
                        [address.latitude, address.longitude],
                        { icon: addressIconInactive } 
                    )
                    return addressMarker.bindPopup(popupText(address))
                })

                addressMarkers
                    .map(m => m.on('popupopen', this.onPopupOpen))
                    .map(m => m.on('popupclose', this.onPopupClose))
                    .map(m => this.addressMarkers.addLayer(m))
            })
    }

    private onPopupOpen(event: PopupEvent) {
        event.target.setIcon(addressIconActive)
    }

    private onPopupClose(event: PopupEvent) {
        event.target.setIcon(addressIconInactive)
    }
}