import { Subject } from 'rxjs'

import { RxCheckboxInput } from './input'
import { animateElementContent } from './common'

/**
 * A boolean (checkbox) facet that can update the count in its <label>.
 * 
 * Assumes that it has an associated <label> element that contains another
 * element (ideally a <span>) with class "count",
 *
 * @class RxBooleanFacet
 * @extends {RxCheckboxInput}
 */
class RxBooleanFacet extends RxCheckboxInput {
    count: Subject<number>
    countElement: HTMLElement | null

    constructor(element: HTMLInputElement) {
        super(element)
        this.count = new Subject()
        // assume the count is an element inside the label with class 'count'
        if (this.label) this.countElement = this.label.querySelector('.count')
        this.count.subscribe(this.updateCount)
    }

    /**
     * Calls animateElementContent() to swap out the content of the count
     * element after its transition-duration.
     * 
     * Returns the locale-string version of the count, which for the en-us
     * locale will insert commas (e.g. 6544 -> 6,544). 
     *
     * @protected
     * @memberof RxBooleanFacet
     */
    protected updateCount = async (count: number): Promise<string> => {
        return animateElementContent(this.element, count.toLocaleString())
    }
}

export {
    RxBooleanFacet,
}