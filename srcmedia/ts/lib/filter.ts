import { Observable, combineLatest } from 'rxjs'
import { filter, map, withLatestFrom, publish, mapTo } from 'rxjs/operators'

import { Rx } from './common'
import { RxNumberInput } from './input'


type Range = [number, number] // Type alias for convenience

/**
 * A range filter consisting of two numeric inputs. The values are only updated
 * when both inputs are valid.
 *
 * @class RxRangeFilter
 * @extends {Rx<HTMLFieldSetElement>}
 */
class RxRangeFilter extends Rx<HTMLFieldSetElement> {

    public value$: Observable<Range>
    public valid$: Observable<boolean>

    private startInput: RxNumberInput
    private stopInput: RxNumberInput

    constructor(element: HTMLFieldSetElement) {
        super(element)
        // detect the <input>s associated with the facet
        const inputs = this.element.getElementsByTagName('input')
        this.startInput = new RxNumberInput(inputs[0])
        this.stopInput = new RxNumberInput(inputs[1])
        // combine the values of the two inputs
        this.value$ = combineLatest(this.startInput.value$, this.stopInput.value$)
        // combine the validity state of the two inputs
        this.valid$ = combineLatest(this.startInput.valid$, this.stopInput.valid$)
            .pipe(
                withLatestFrom(this.value$), // grab the values so we can check start <= stop
                map(([[startValid, stopValid], [start, stop]]) => { // do the actual check; returns bool
                    return ((start || -Infinity) <= (stop || Infinity)) && // only compare start < stop if they have values (not NaN)
                    (startValid && stopValid) // both must also be valid
                })
            )
    }
}

export {
    Range,
    RxRangeFilter,
}