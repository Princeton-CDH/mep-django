import Tablesort from 'tablesort'
import { sortItem, compareItem } from './lib/sort'

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
})