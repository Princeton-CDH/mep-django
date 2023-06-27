import { Observable, Subject, fromEvent, merge, combineLatest } from 'rxjs'
import { map, filter, distinctUntilChanged, withLatestFrom, skip } from 'rxjs/operators'

import { RxCheckboxInput, RxNumberInput } from './input'
import { Rx, animateElementContent, arraysAreEqual } from './common'

export type Choice = [string, number]

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
        if (this.label) {
            this.countElement = this.label.querySelector('.count')
            this.count.subscribe(this.updateCount)
        }
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
        if (this.countElement) {
            return animateElementContent(this.countElement, count.toLocaleString())
        }
        return count.toLocaleString()
    }
}

/**
 * A choice facet consisting of multiple checkboxes where the user always
 * has access to all the choices.
 *
 * This facet is similar to a text facet, but intended for use where there are
 * a limited number of choices that should always be displayed, regardless
 * of counts.
 *
 * @class RxChoiceFacet
 * @extends {Rx<HTMLFieldSetElement>}
 */
class RxChoiceFacet extends Rx<HTMLFieldSetElement> {

    protected $inputs: Array<HTMLInputElement>
    public counts: Subject<[string, number]> // input from solr
    public events: Observable<Event>

    constructor (element: HTMLFieldSetElement) {
        super(element)
        // find and save all the <input>s associated with this facet
        this.$inputs = Array.from(this.element.getElementsByTagName('input'))
        this.counts = new Subject()
        // keep track of the user's selections so we can tell the form to update
        // note that mobile safari doesn't support 'input' here so we use 'change'
        this.events = merge(...this.$inputs.map($input => fromEvent($input, 'change')))
        this.counts.subscribe(this.updateCount)
    }

    /**
     * Finds the relevant count element for each choice input and calls
     * animateElementContent() to swap out the number displayed in it.
     *
     * Assumes the input has exactly one <label> that contains a <span> with
     * class 'count'.
     *
     * @protected
     * @memberof RxChoiceFacet
     */
    protected updateCount = async ([label, count]: [string, number]): Promise<void> => {
        const value = (label == 'null' ? '' : label) // solr 'null' becomes empty value ""
        const $input = this.$inputs.find($input => $input.value == value)
        //@ts-ignore
        const $count = $input.labels[0].querySelector('.count') as HTMLSpanElement
        await animateElementContent($count, count.toLocaleString())
    }
}

/**
 * A text facet consisting of multiple checkboxes where the user will see a
 * choice if its count is above a provided threshold.
 *
 * When new counts are supplied, options will be shown or hidden accordingly.
 * Note that this means they must all be *rendered* by the backend first!
 *
 * @class RxTextFacet
 * @extends {Rx<HTMLFieldSetElement>}
 */
class RxTextFacet extends RxChoiceFacet {

    // choices with counts <= this number will be hidden, if supplied
    private threshold: number | undefined

    constructor (element: HTMLFieldSetElement) {
        super(element)
        // use a different updateCount() method - see below
        this.counts.subscribe(this.updateCount)
        // if a hide threshold was set, store it
        if (this.element.dataset.hideThreshold) {
            this.threshold = parseInt(this.element.dataset.hideThreshold, 10)
        }
    }

    /**
     * Finds the relevant count element for each choice input and calls
     * animateElementContent() to swap out the number displayed in it.
     *
     * Assumes the input has exactly one <label> that contains a <span> with
     * class 'count'.
     *
     * @protected
     * @memberof RxChoiceFacet
     */
    protected updateCount = async ([label, count]: [string, number]): Promise<void> => {
        const value = (label == 'null' ? '' : label) // solr 'null' becomes empty value ""
        const $input = this.$inputs.find($input => $input.value == value)
        //@ts-ignore
        const $count = $input.labels[0].querySelector('.count') as HTMLSpanElement
        // if the count fell below the threshold, add "hide" to the choice
        if (this.threshold != undefined) {
            const $choice = ($input as HTMLElement).parentElement as HTMLLabelElement
            if (count <= this.threshold) {
                $choice.classList.add('hide')
            }
            else {
                $choice.classList.remove('hide')
            }
        }
        await animateElementContent($count, count.toLocaleString())
    }
}

export {
    RxBooleanFacet,
    RxChoiceFacet,
    RxTextFacet
}
