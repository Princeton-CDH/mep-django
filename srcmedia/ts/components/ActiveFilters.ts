import { Component } from '../lib/common'
import { fakeToggle, fakeValueChange } from '../lib/common'

type Filters = Map<string, any>

export default class ActiveFilters extends Component {
    $form: HTMLFormElement         // form whose filters we want to track
    $legend: HTMLElement           // 'active filters' text
    $clearAll: HTMLAnchorElement   // 'clear all' button

    constructor(element: HTMLElement) {
        super(element)

        // find the containing form and store
        const form = this.element.closest('form')
        if (!form) console.error(`No containing form found for ${element}`)
        else this.$form = form

        // find the legend and store
        const legend = this.element.querySelector('.legend')
        if (!legend) console.error(`No .legend element found in ${element}`)
        else this.$legend = (legend as HTMLElement)

        // find the 'clear all' button and store
        const clearAll = this.element.querySelector('.clear-all')
        if (!clearAll) console.error(`No .clear-all element found in ${element}`)
        else this.$clearAll = (clearAll as HTMLAnchorElement)

        // turn all links currently inside the element into buttons w/ handlers
        const $anchors = this.element.querySelectorAll('a')
        $anchors.forEach(($anchor: HTMLAnchorElement) => {
            $anchor.removeAttribute('href')
            $anchor.setAttribute('role', 'button')
            ActiveFilters.bindClearHandler($anchor)
        })
    }

    /**
     * Given an anchor element (in this case we use <a> as buttons), binds a
     * click handler that clears the input whose id is stored in the data-input
     * attribute of the anchor element.
     * 
     * Handler clears the provided input element, either by untoggling or 
     * removing its current value. Dispatches the appropriate event as though
     * the user had cleared it manually.
     * 
     * @param $button 
     */
    static bindClearHandler($button: HTMLAnchorElement): void {
        const inputId = $button.dataset.input

        if (!inputId) {
            console.error(`No associated input for ${$button}`)
            return
        }

        // add event handler to toggle associated input
        else {
            const $input = document.getElementById(inputId) as HTMLInputElement

            if (!$input) {
                console.error(`Couldn't find element #${inputId}`)
                return
            }

            $button.addEventListener('click', () => {
                if ($input.type == 'checkbox') fakeToggle($input)
                else fakeValueChange($input, '')
            })
        }
    }

    /**
     * Parse the current querystring into a data structure representing active
     * filters. Collapses ranges and multivalued fields into arrays stored at
     * the same key.
     */
    public filters(): Filters {
        const data = new FormData(this.$form)
        const filters: Filters = new Map()

        for (let [key, val] of data.entries()) {
            // collapse ranges into a single entry
            const matchRange = key.match(/^(.*)_\d+$/)
            key = matchRange ? matchRange[1] : key
            
            // store multivalued facets/filters in an array
            const current = filters.get(key)
            if (!current) filters.set(key, val)
            else if (Array.isArray(current))
                filters.set(key, [...current, val])
            else filters.set(key, [current, val])
        }

        return filters
    }

    /**
     * Fill the element with buttons that correspond to the provided list of
     * filters. Clicking each button removes it and emits an event that can be
     * used to update the state of the corresponding filter.
     * 
     * @param filters 
     */
    public render(filters: Filters) {
        filters.forEach((val, key) => {
            // create the button
            const $button = document.createElement('a')
            $button.setAttribute('role', 'button')
            $button.innerText = key

            // TODO create the event handler

            // add it to the inside of the element
            this.$clearAll.insertBefore($button, null)
        })
    }
}