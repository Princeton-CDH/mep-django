import { fromEvent, Subject } from 'rxjs'
import { map } from 'rxjs/operators'

import { Component, Reactive } from './common'

interface RxSelectState {
    value: string
}

class RxSelect extends Component implements Reactive<RxSelectState> {
    element: HTMLSelectElement
    state: Subject<RxSelectState>

    constructor(element: HTMLSelectElement) {
        super(element)
        this.state = new Subject()
        this.update = this.update.bind(this)
        // Update state when the user selects a new value
        fromEvent(this.element, 'input').pipe(
            map(() => ({ value: this.element.value }))
        ).subscribe(this.update)
    }

    /**
     * Update state and propagate changes to the <select> element.
     *
     * @param {RxSelectState} state
     * @returns {Promise<void>}
     * @memberof RxSelect
     */
    async update(newState: Partial<RxSelectState>): Promise<void> {
        if (newState.value) this.element.value = newState.value
        this.state.next({ value: this.element.value })
    }
}

export {
    RxSelect,
    RxSelectState
}