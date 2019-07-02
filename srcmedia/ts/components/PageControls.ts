import { Subject, merge, fromEvent } from 'rxjs'
import { mapTo } from 'rxjs/operators'

import StickyControls from './StickyControls'

/**
 * A sort/pagination control component that applies a css class when it's stuck
 * to the top of the page.
 */
export default class PageControls extends StickyControls {
    nextButton: HTMLAnchorElement
    prevButton: HTMLAnchorElement
    pageChanges: Subject<string>

    constructor(element: HTMLElement) {
        super(element)
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
     * Sets the aria-hidden states on the next/prev page controls based on
     * whether the user has a next or previous page available to select.
     *
     * @memberof PageControls
     */
    update = async ([currentPage, totalPages]: [number, number]): Promise<void> => {
        // assume next and previous buttons are enabled by default
        let nextEnabled = true,
            previousEnabled = true;

        if (currentPage == 1) { // if on first page, no previous
            previousEnabled = false;
        }
        if (currentPage == totalPages) {  // if on last page, no next
            nextEnabled = false;
        }
        // also handles single page of results, which is both 1 and last page

        // hide or enable next and previous based on the determined status
        if (nextEnabled) {
            this.nextButton.removeAttribute('aria-hidden')
        } else {
            this.nextButton.setAttribute('aria-hidden', '')
        }
        if (previousEnabled) {
            this.prevButton.removeAttribute('aria-hidden')
        } else {
            this.prevButton.setAttribute('aria-hidden', '')
        }

    }
}