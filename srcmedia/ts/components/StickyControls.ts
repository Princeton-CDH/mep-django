import { mapTo } from 'rxjs/operators'

import { Component } from '../lib/common'

/**
 * A component that applies a css class when it's stuck to the top of the page.
 */
export default class StickyControls extends Component {
    element: HTMLElement
    ticking: boolean = false
    stuck: boolean = false
    top: number = 0

    constructor(element: HTMLElement) {
        super(element)
        // Get the top property
        let top = window
            .getComputedStyle(this.element)
            .getPropertyValue('top')
        // Convert a css value like '50px' to integer pixels
        if (top) this.top = parseFloat(top)
        // Bind a scroll event listener to check if sticking
        window.addEventListener('scroll', this.scroll.bind(this))
    }

    /**
     * Event handler for scroll events that checks if the element is sticking
     * to its specified top value. Uses requestAnimationFrame to avoid making
     * needless calls and improve performance.
     */
    scroll(): void {
        if (!this.ticking) {
            window.requestAnimationFrame(() => {
                if (this.element.getBoundingClientRect().top == this.top && !this.stuck) {
                    this.stick()
                }
                else if (this.element.getBoundingClientRect().top != this.top && this.stuck) {
                    this.unstick()
                }
                this.ticking = false
            })
            this.ticking = true
        }
    }

    /**
     * Applies the 'stuck' class to indicate the element is currently sticking.
     */
    stick(): void {
        this.stuck = true
        this.element.classList.add('stuck')
    }

    /**
     * Removes the 'stuck' class to indicate the element is no longer sticking.
     */
    unstick(): void {
        this.stuck = false
        this.element.classList.remove('stuck')
    }

}