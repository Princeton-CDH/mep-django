import StickyControls from '../components/StickyControls'

document.addEventListener('DOMContentLoaded', () => {

    /* ELEMENTS */
    const $tableHeader = document.getElementsByTagName('th')[0] as HTMLElement
    const $activeCard = document.querySelector('.card.active') as HTMLLIElement
    const $cardNav = document.querySelector('nav.cards') as HTMLElement

    /* COMPONENTS */

    // bind to header element but set stuck class on the table header
    // const stickyControls = new StickyControls($tableHeaderElement, $tableHeader)
    if ($tableHeader) new StickyControls($tableHeader)

    /* BINDINGS */
    scrollToActiveCard($cardNav, $activeCard)
})

/**
 * Automatically scroll the card navigation to focus the currently viewed card.
 * 
 * @param nav 
 * @param activeCard 
 */
function scrollToActiveCard(nav: HTMLElement, activeCard: HTMLLIElement): void {
    // distance we want to scroll is (offset - card width - margin)px
    const style = getComputedStyle(activeCard)
    const margin = style.marginRight ? parseInt(style.marginRight.split('px')[0]) : 0
    nav.scroll(activeCard.offsetLeft - activeCard.offsetWidth - margin, 0)
}