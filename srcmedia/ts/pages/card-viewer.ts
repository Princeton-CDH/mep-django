import StickyControls from '../components/StickyControls'

document.addEventListener('DOMContentLoaded', () => {

    /* ELEMENTS */
    const $tableHeader = document.getElementsByTagName('th')[0] as HTMLElement

    /* COMPONENTS */

    // bind to header element but set stuck class on the table header
    // const stickyControls = new StickyControls($tableHeaderElement, $tableHeader)
    new StickyControls($tableHeader)
})