import { fromEvent, Observable } from 'rxjs'
import { map, startWith, share } from 'rxjs/operators'

import { Rx } from './common'

/**
 * An ancestor for all reactive `<input>` elements. These elements should always
 * have a `type` attribute, so the class is abstract.
 * 
 * Reactivity is based on UIEvents of type EVENT_TYPE, which will update the
 * input's validity and (in ancestor classes) other properties like `value`.
 *
 * @abstract
 * @class RxInput
 * @extends {Rx<HTMLInputElement>}
 */
abstract class RxInput extends Rx<HTMLInputElement> {
    // Observables
    public valid$: Observable<boolean>
    public events$: Observable<UIEvent>
    
    // Local data
    protected label: HTMLLabelElement | null
    protected readonly EVENT_TYPE: string = 'input' // defaults to 'input' but some inputs will use 'change'

    constructor(element: HTMLInputElement) {
        super(element)
        this.label = this.element.labels ? this.element.labels[0] : null // use the first label, if any
        this.events$ = fromEvent(this.element, this.EVENT_TYPE) as Observable<UIEvent> // cast here because we know the specific Event subclass
        this.valid$ = this.events$.pipe(
            map(() => this.element.checkValidity()), // update validity when events of EVENT_TYPE occur
            startWith(this.element.checkValidity()), // start with current value
            share() // multicast
        )
    }
}

/**
 * A reactive `<input type="text">` element. Stores its `value` as an observable
 * `string`.
 *
 * @class RxTextInput
 * @extends {RxInput}
 */
class RxTextInput extends RxInput {

    public value$: Observable<string>

    constructor(element: HTMLInputElement) {
        super(element)
        this.value$ = this.events$.pipe(
            map(() => this.element.value),
            startWith(this.element.value),
            share()
        )
    }
}

/**
 * A reactive `<input type="number">` element. Stores its `value` as an
 * observable `number`. Non-integer values will be parsed to `NaN`.
 *
 * @class RxNumberInput
 * @extends {RxInput}
 */
class RxNumberInput extends RxInput {

    public value$: Observable<number>

    constructor(element: HTMLInputElement) {
        super(element)
        this.value$ = this.events$.pipe(
            map(() => this.element.value),
            map(value => parseInt(value)), // will return NaN if not an integer
            startWith(parseInt(this.element.value)),
            share()
        )
    }
}

/**
 * A reactive `<input type="checkbox">` element. Stores its checked state as an
 * observable `boolean`.
 *
 * @class RxCheckboxInput
 * @extends {RxInput}
 */
class RxCheckboxInput extends RxInput {

    public checked$: Observable<boolean>

    protected readonly EVENT_TYPE: string = 'change' // use the 'change' event for legacy compatibility

    constructor(element: HTMLInputElement) {
        super(element)
        this.checked$ = this.events$.pipe(
            map(() => this.element.checked),
            startWith(this.element.checked),
            share()
        )
    }
}

export {
    RxInput,
    RxCheckboxInput,
    RxTextInput,
    RxNumberInput
}