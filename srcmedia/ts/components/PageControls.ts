import { Subject, merge, fromEvent } from 'rxjs'
import { mapTo } from 'rxjs/operators'

import { Component } from '../lib/common'

/**
 * A sort/pagination control component that applies a css class when it's stuck
 * to the top of the page.
 */
export default class PageControls extends Component {
    element: HTMLElement
    nextButton: HTMLAnchorElement
    prevButton: HTMLAnchorElement
    pageChanges: Subject<string>
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
        // Set up page change event tracking
        this.pageChanges = new Subject()
        // Find the next and previous links
        this.nextButton = this.element.querySelector('a[rel=next]') as HTMLAnchorElement
        this.prevButton = this.element.querySelector('a[rel=prev]') as HTMLAnchorElement
        // Convert them into buttons
        this.nextButton.removeAttribute('href')
        this.prevButton.removeAttribute('href')
        this.nextButton.setAttribute('role', 'button')
        this.prevButton.setAttribute('role', 'button')
        this.nextButton.setAttribute('tabindex', '0')
        this.prevButton.setAttribute('tabindex', '0')
        // Listen to click events on the buttons
        // Note the use of mapTo here: we don't care about the actual event,
        // just want to emit a constant value
        merge(
            fromEvent(this.nextButton, 'click').pipe(mapTo('next')),
            fromEvent(this.prevButton, 'click').pipe(mapTo('prev'))
        ).subscribe(this.pageChanges)
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

    /**
     * Sets the aria-hidden states on the next/prev page controls based on
     * whether the user has a next or previous page available to select.
     *
     * @memberof PageControls
     */
    update = async ([currentPage, totalPages]: [number, number]): Promise<void> => {
        if (currentPage == totalPages) {
            this.prevButton.removeAttribute('aria-hidden')
            this.nextButton.setAttribute('aria-hidden', '')
        }
        else if (currentPage == 1) {
            this.nextButton.removeAttribute('aria-hidden')
            this.prevButton.setAttribute('aria-hidden', '')
        }
        else {
            this.nextButton.removeAttribute('aria-hidden')
            this.prevButton.removeAttribute('aria-hidden')
        }
    }
}