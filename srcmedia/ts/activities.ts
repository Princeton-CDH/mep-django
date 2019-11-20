import Tablesort from 'tablesort'
import { sortItem, compareItem } from './lib/sort'
import { setAllHeights } from './lib/common'

import StickyControls from './components/StickyControls'

// enable numeric sorting in Tablesort
Tablesort.extend('number', sortItem, compareItem)

document.addEventListener('DOMContentLoaded', () => {

    /* ELEMENTS */
    const $table = document.getElementById('activity-table') as HTMLElement
    const $form = document.getElementById('activity-mobile-control') as HTMLElement
    const $expand = document.getElementById('expand') as HTMLFormElement
    const $events = document.getElementsByTagName('tr') as HTMLCollection

    const $tableHeader = document.getElementsByTagName('thead')[0] as HTMLElement
    const $tableHeaderElement = document.getElementsByTagName('th')[0] as HTMLElement

    /* COMPONENTS */
    // bind to header element but set stuck class on the table header
    // const stickyControls = new StickyControls($tableHeaderElement, $tableHeader)
    const stickyControls = new StickyControls($tableHeaderElement)

    Tablesort($table)

    /* BINDINGS */
    // on tablet only, we need to manually set row heights so that the leftmost
    // table column can be sticky
    if (window.matchMedia('(min-width: 768px) and (max-width: 1023px)').matches) {
        const firsts = document.querySelectorAll('td.title') as NodeListOf<HTMLTableCellElement>
        firsts.forEach(e => {
            const start = e.nextElementSibling as HTMLElement
            setAllHeights(start, getComputedStyle(e).getPropertyValue('height'))
        })
    }
})