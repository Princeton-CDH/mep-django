import { Rx } from '../lib/common'
import { Observable, of } from 'rxjs'
import { publishBehavior } from 'rxjs/operators'

type State = Map<String, any>

export default class ActiveFilters extends Rx<HTMLElement> {
    $legend: HTMLElement           // 'active filters' text
    $clearAll: HTMLAnchorElement   // 'clear all' button
    filters: Observable<State>     // list of currently active filters

    constructor(element: HTMLElement) {
        super(element)

        // find the legend and clear-all buttons and store
        this.$legend = this.element.querySelector('.legend') as HTMLElement
        this.$clearAll = this.element.querySelector('.clear-all') as HTMLAnchorElement

        // turn all links currently inside the element into buttons
        const $anchors = this.element.querySelectorAll('a')
        $anchors.forEach(($anchor: HTMLAnchorElement) => {
            $anchor.removeAttribute('href')
            $anchor.setAttribute('role', 'button')
        })

        // parse the querystring and set the initial state of activeFilters
        const params = new URLSearchParams(window.location.search)
        const initFilters: State = new Map()

        for (let [key, val] of params.entries()) {
            // collapse ranges into a single entry
            const matchRange = key.match(/^(.*)_\d+$/)
            key = matchRange ? matchRange[1] : key

            // store multivalued facets/filters in an array
            const current = initFilters.get(key)
            if (!current) initFilters.set(key, val)
            else if (Array.isArray(current))
                initFilters.set(key, [...current, val])
            else initFilters.set(key, [current, val])
        }

        // multicast the state and start with the initial value
        this.filters = of(initFilters).pipe(publishBehavior(initFilters))

        // re-render when state changes
        this.filters.subscribe(this.render)
    }

    private render(filters: State) {
        // this.$clearAll.insertAdjacentElement('beforebegin', )
    }
}