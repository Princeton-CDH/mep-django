/**
 * A main menu component that can show/hide itself relative to the document
 * body using opacity and z-index.
 */
export default class MainMenu {
    element: HTMLElement
    transitionDuration: number

    constructor(element: HTMLElement) {
        this.element = element
        // Get the transition-duration property
        let td = window
            .getComputedStyle(this.element)
            .getPropertyValue('transition-duration')
        // Convert a css value like '0.5s' or '200ms' to integer milliseconds
        // If none was specified (NaN), use zero
        this.transitionDuration = 
            td ? parseFloat(td) * (/\ds$/.test(td) ? 1000 : 1) : 0
    }

    /**
     * Open/show the main menu. Returned Promise resolves after the transition
     * duration specified in CSS, or immediately if none specified.
     * 
     * @param event click event on #open-main-menu
     */
    async show(event: MouseEvent): Promise<void> {
        event.preventDefault()
        this.element.style.zIndex = '100'
        this.element.style.opacity = '1'
        this.element.style.pointerEvents = 'all'
        document.body.style.overflowY = 'hidden'
        return new Promise(resolve => setTimeout(resolve, this.transitionDuration))
    }

    /**
     * Close/hide the main menu. Returned Promise resolves after the transition
     * duration specified in CSS, or immediately if none specified.
     * 
     * @param event click event on #close-main-menu
     */
    async hide(event: MouseEvent): Promise<void> {
        event.preventDefault()
        this.element.style.zIndex = '-100'
        this.element.style.opacity = '0'
        this.element.style.pointerEvents = 'none'
        document.body.style.overflowY = null
        return new Promise(resolve => setTimeout(resolve, this.transitionDuration))
    }
}