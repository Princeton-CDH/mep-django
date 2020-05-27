import { map, Map, control, marker, Marker, featureGroup, PopupEvent, markerClusterGroup } from 'leaflet'
import 'leaflet.markercluster'

import { Address, getMapboxBasemap, getParisTileLayer, bookstoreIcon, addressIconActive, addressIconInactive, popupText } from '../lib/map'
import addressData from '../lib/map-data'

declare const mapboxToken: string
declare const mapboxBasemap: string
declare const parisOverlay: string

export default class MemberSearchMap {

    private readonly ADDRESS_DATA_URL: '/foo'

    private map: Map
    private library: Address
    private libraryMarker: Marker
    private addresses: Address[]
    private addressMarkers: Marker[]

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

        // add all active address markers
        this.update()

        // add library marker on top of address markers
        this.libraryMarker = marker([this.library.latitude, this.library.longitude], {
            icon: bookstoreIcon,
            zIndexOffset: 1000,
        })
        .bindPopup(popupText(this.library))
        .addTo(this.map)
    }

    update() {
        // TODO hit the URL for data
        const { addresses, members } = addressData

        this.addressMarkers = addresses.map((address: Address) => {

            const addrMarker: Marker = marker(
                [address.latitude, address.longitude],
                { icon: addressIconInactive }
            )
            
            addrMarker.bindPopup(popupText(address))
            /*
            if (address.member_slugs) {
                //@ts-ignore
                let member = members[address.member_slugs[0]]
                if (member && member.sort_name) {
                    addrMarker.bindTooltip(member.sort_name, { permanent: true })
                    addrMarker.openTooltip()
                }
            }
            */

            return addrMarker
        })

        const group = markerClusterGroup({
            showCoverageOnHover: false,
            maxClusterRadius: 40,
        })

        this.addressMarkers
            .map(m => m.on('popupopen', this.onPopupOpen))
            .map(m => m.on('popupclose', this.onPopupClose))
            .map(m => group.addLayer(m))

        this.map.addLayer(group)
    }

    private onPopupOpen(event: PopupEvent) {
        event.target.setIcon(addressIconActive)
    }

    private onPopupClose(event: PopupEvent) {
        event.target.setIcon(addressIconInactive)
    }
}