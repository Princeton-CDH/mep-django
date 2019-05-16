import { Observable, Subject, fromEvent, merge, combineLatest } from 'rxjs'
import { map, filter, distinctUntilChanged, withLatestFrom } from 'rxjs/operators'

import { RxCheckboxInput, RxNumberInput } from './input'
import { Rx, animateElementContent } from './common'

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
 * A range facet consisting of two numeric inputs. No counts are shown.
 * Note that this technically makes it a filter, rather than a facet.
 * 
 * The values are only updated when both inputs are a valid and unique combination
 * of numbers.
 *
 * @class RxRangeFacet
 * @extends {Rx<HTMLFieldSetElement>}
 */
class RxRangeFacet extends Rx<HTMLFieldSetElement> {

    protected inputs: Array<RxNumberInput>
    public values: Observable<Array<number>>

    constructor(element: HTMLFieldSetElement) {
        super(element)
        // find the <input>s associated with the facet
        this.inputs = Array.from(this.element.getElementsByTagName('input'))
            .map($input => new RxNumberInput($input))
        // keep track of user's changes so we can tell the form to update
        this.values = combineLatest(
            ...this.inputs.map(i => { // for each input,
                return i.value.pipe( // update when the value updates
                    // NOTE potentially a more elegant way to do this...probably
                    // just a different operator would suffice
                    withLatestFrom(i.valid), // only pass through value if valid
                    filter(([value, valid]) => valid),
                    map(([value, valid]) => value),
                )
            })
        ).pipe(distinctUntilChanged()) // only unique combinations of inputs
    }

}

export {
    RxBooleanFacet,
    RxChoiceFacet,
    RxRangeFacet
}