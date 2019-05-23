import { Observable, combineLatest } from 'rxjs'
import { filter, map, withLatestFrom, distinctUntilChanged } from 'rxjs/operators'

import { Rx, arraysAreEqual } from './common'
import { RxNumberInput } from './input'

/**
 * A range filter consisting of two numeric inputs. The values are only updated
 * when both inputs are valid.
 *
 * @class RxRangeFilter
 * @extends {Rx<HTMLFieldSetElement>}
 */
class RxRangeFilter extends Rx<HTMLFieldSetElement> {

    protected inputs: Array<RxNumberInput>
    public values: Observable<Array<number>>
    public valid: Observable<boolean>

    constructor(element: HTMLFieldSetElement) {
        super(element)
        // find the <input>s associated with the facet
        this.inputs = Array.from(this.element.getElementsByTagName('input'))
            .map($input => new RxNumberInput($input))
        // combine the validity state of the two inputs
        this.valid = combineLatest(
            ...this.inputs.map(i => i.value.pipe(withLatestFrom(i.valid)))
        ).pipe(
            filter(([[value1, valid1], [value2, valid2]]) => valid1 && valid2), // both valid
            map(([[value1, valid1], [value2, valid2]]) => {
                return (value1 || -Infinity) <= (value2 || Infinity) // if not empty, min <= max
            }),
        )
        // keep track of user's changes so we can tell the form to update
        this.values = combineLatest(
            ...this.inputs.map(i => i.value)
        ).pipe(
            withLatestFrom(this.valid), // check that the facet is valid
            filter(([[value1, value2], valid]) => valid),
            map(([[value1, value2], valid]) => [value1, value2]), // don't need validity info
            distinctUntilChanged(arraysAreEqual), // only unique combinations of inputs
        )
        // set an "error" class depending on if we're valid or not
        this.valid.subscribe(valid => {
            valid ?
                this.element.classList.remove('error') :
                this.element.classList.add('error')
        })
    }
}

export {
    RxRangeFilter,
}