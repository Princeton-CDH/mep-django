import { fromEvent, Subject, Observable } from 'rxjs'
import { map, debounceTime, distinctUntilChanged, startWith } from 'rxjs/operators'

import { Component, Reactive, Rx } from './common'

interface RxInputState { // basic state common to all <input> types
    value: string
}


interface RxTextInputState extends RxInputState { // no special fields
}

interface RxCheckboxInputState extends RxInputState {
    checked: boolean
}

/**
 * An ancestor for all reactive <input> elements. These elements should always
 * have a `type` attribute, so the class is abstract.
 *
 * The update() method has a default implementation that updates the `value` and
 * `name` attributes; simple types of <input> may not need to override it.
 *
 * @abstract
 * @class RxInput
 * @extends {Component}
 * @implements {Reactive<RxInputState>}
 */
abstract class RxInput extends Component implements Reactive<RxInputState> {
    element: HTMLInputElement
    state: Subject<RxInputState>
    label: HTMLLabelElement | null

    constructor(element: HTMLInputElement) {
        super(element)
        this.label = this.element.labels ? this.element.labels[0] : null
        this.state = new Subject()
        this.update = this.update.bind(this) // callers need access to `this`
    }

    /**
     * Update state and propagate changes to the <input> element.
     *
     * @param {RxInputState} state
     * @returns {Promise<void>}
     * @memberof RxInput
     */
    update = async (newState: Partial<RxInputState>): Promise<void> => {
        if (newState.value) this.element.value = newState.value
        this.state.next({ value: this.element.value })
    }
}

/**
 * A reactive <input type="text"> element.
 *
 * @class RxTextInput
 * @extends {RxInput}
 * @implements {Reactive<RxTextInputState>}
 */
class RxTextInput extends RxInput implements Reactive<RxTextInputState> {
    state: Subject<RxTextInputState>

    constructor(element: HTMLInputElement) {
        super(element)
        // Update state when the user types in a new value, with debounce
        fromEvent(this.element, 'input').pipe(
            map(() => ({ value: this.element.value })),
            debounceTime(500),
            distinctUntilChanged()
        ).subscribe(this.update)
    }
}

/**
 * A reactive <input type="number"> element.
 *
 * Publishes its validity state and current value; invalid values will be
 * parsed to NaN.
 *
 * @class RxNumberInput
 * @extends {Rx<HTMLInputElement>}
 */
class RxNumberInput extends Rx<HTMLInputElement> {

    public value: Observable<number>
    public valid: Observable<boolean>

    constructor(element: HTMLInputElement) {
        super(element)
        // Update state when the user types in a new value, with debounce
        this.value = fromEvent(this.element, 'input').pipe(
            map(() => parseInt(this.element.value)),
            debounceTime(500),
            distinctUntilChanged(),
        )
        // Update validity based on when value changes
        this.valid = this.value.pipe(
            map(() => this.element.checkValidity()),
            distinctUntilChanged(),
        )
    }
}

/**
 * A reactive <input type="checkbox"> element.
 *
 * @class RxCheckboxInput
 * @extends {RxInput}
 * @implements {Reactive<RxCheckboxInputState>}
 */
class RxCheckboxInput extends RxInput implements Reactive<RxCheckboxInputState>{
    state: Subject<RxCheckboxInputState>

    constructor(element: HTMLInputElement) {
        super(element)
        // Update state immediately when the checkbox is clicked
        fromEvent(this.element, 'change').pipe(
            map(() => ({ checked: this.element.checked })),
        ).subscribe(this.update)
    }

    /**
     * Update state and propagate changes to the checkbox element.
     *
     * @param {RxCheckboxInputState} state
     * @returns {Promise<void>}
     * @memberof RxCheckboxInput
     */
    update = async (newState: Partial<RxCheckboxInputState>): Promise<void> => {
        if (newState.value) this.element.value = newState.value
        if (newState.checked) this.element.checked = newState.checked
        this.state.next({
            value: this.element.value,
            checked: this.element.checked
        })
    }
}

export {
    RxInput,
    RxCheckboxInput,
    RxTextInput,
    RxNumberInput
}