import { fromEvent, Subject } from 'rxjs'
import { map } from 'rxjs/operators'

import { Component, Reactive } from './common'

interface RxSelectState {
    value: string
}

/**
 * A reactive <select> element that emits its current value when changed.
 * 
 * @class RxSelect
 * @extends {Component}
 * @implements {Reactive<RxSelectState>}
 */
class RxSelect extends Component implements Reactive<RxSelectState> {
    element: HTMLSelectElement
    state: Subject<RxSelectState>

    constructor(element: HTMLSelectElement) {
        super(element)
        this.state = new Subject()
        // Update state when the user selects a new value
        fromEvent(this.element, 'input').pipe(
            map(() => ({ value: this.element.value })),
        ).subscribe(this.update)
    }

    /**
     * Update state and propagate changes to the <select> element.
     *
     * @param {RxSelectState} state
     * @returns {Promise<void>}
     * @memberof RxSelect
     */
    update = async (newState: RxSelectState): Promise<void> => {
        if (newState.value) this.element.value = newState.value
        this.state.next({ value: newState.value })
    }
}

export {
    RxSelect,
    RxSelectState
}