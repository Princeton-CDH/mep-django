import { getTransitionDuration } from '../lib/common'

/**
 * A main menu component that can show/hide itself relative to the document
 * body using opacity and z-index.
 */
export default class MainMenu {
    element: HTMLElement
    transitionDuration: number = 0

    constructor(element: HTMLElement) {
        this.element = element
        this.transitionDuration = getTransitionDuration(this.element)
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
        this.element.style.display = 'block'
        this.element.style.pointerEvents = 'all'
        this.element.removeAttribute('aria-hidden')
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
        this.element.style.display = 'none'
        this.element.style.pointerEvents = 'none'
        this.element.setAttribute('aria-hidden', 'true')
        document.body.style.overflowY = ''
        return new Promise(resolve => setTimeout(resolve, this.transitionDuration))
    }
}