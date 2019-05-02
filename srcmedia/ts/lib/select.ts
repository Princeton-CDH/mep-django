import { fromEvent, Subject } from 'rxjs'
import { map } from 'rxjs/operators'

import { Component } from './common'

interface RxOption {
    value: string,
    text: string,
}

/**
 * A reactive <select> element that emits its current value when changed.
 * 
 * @class RxSelect
 * @extends {Component}
 * @implements {Reactive<RxSelectState>}
 */
class RxSelect extends Component {
    element: HTMLSelectElement
    value: Subject<string>
    options: Subject<Array<RxOption>>
    disabled: Subject<boolean>

    constructor (element: HTMLSelectElement) {
        super(element)
        this.value = new Subject()
        this.options = new Subject()
        this.disabled = new Subject()
        // Update value when the user selects a new value
        fromEvent(this.element, 'input').pipe(
            map(() => this.element.value),
        ).subscribe(this.value)
        // Update element when a new value is passed in
        this.value.subscribe(value => this.element.value = value)
        // Re-render options when options are updated
        this.options.subscribe(this.render)
        // Set the 'disabled' attribute when changed
        this.disabled.subscribe(disabled => this.element.disabled = disabled)
    }

    /**
     * Render a new set of <options> for this <select>.
     * 
     * @param {Array<RxOption>} options
     * @returns {Promise<void>}
     * @memberof RxSelect
     */
    render = async (options: Array<RxOption>): Promise<void> => {
        // clear out the options
        this.element.innerHTML = ''
        // render new options and add them to the element
        options.map(this.createOption).forEach(e => this.element.add(e))
    }

    /**
     * Generate and return an <option> element with a given value and text.
     *
     * @protected
     * @param {RxOption} option
     * @returns {HTMLOptionElement}
     * @memberof RxSelect
     */
    protected createOption (option: RxOption): HTMLOptionElement {
        let $el = document.createElement('option')
        $el.value = option.value
        $el.innerHTML = option.text
        return $el
    }
}

export {
    RxSelect,
    RxOption
}