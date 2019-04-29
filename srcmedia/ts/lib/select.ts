import { fromEvent, Subject } from 'rxjs'
import { map } from 'rxjs/operators'

import { Component } from './common'

interface RxOption {
    value: string,
    text: string,
    selected: boolean,
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

    constructor (element: HTMLSelectElement) {
        super(element)
        this.value = new Subject()
        this.options = new Subject()
        // Update value when the user selects a new value
        fromEvent(this.element, 'input').pipe(
            map(() => this.element.value),
        ).subscribe(this.value)
        // Update element when a new value is passed in
        this.value.subscribe(value => this.element.value = value)
        // Re-render options when options are updated
        this.options.subscribe(this.render)
    }

    render = async (options: Array<RxOption>): Promise<void> => {
        // clear out the options
        this.element.innerHTML = ''
        // render new options and add them to the element
        options.map(RxSelect.createOption).forEach(e => this.element.add(e))
    }

    static createOption (option: RxOption): HTMLOptionElement {
        let $el = document.createElement('option')
        $el.value = option.value
        $el.innerHTML = option.text
        $el.selected = option.selected
        return $el
    }
}

export {
    RxSelect,
    RxOption
}