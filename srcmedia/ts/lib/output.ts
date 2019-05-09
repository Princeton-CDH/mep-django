import { Subject } from 'rxjs'

import { Component, Reactive } from '../lib/common'

// State represented as just a string for now, e.g. for html responses
type RxOutputState = string

/**
 * A reactive <output> element that simply renders its state as a string as
 * the element's innerHTML. Useful for displaying metrics or results.
 *
 * @class RxOutput
 * @extends {Component}
 * @implements {Reactive<RxOutputState>}
 */
class RxOutput extends Component implements Reactive<RxOutputState> {
    state: Subject<RxOutputState>

    constructor(element: HTMLOutputElement) {
        super(element)
        this.state = new Subject()
        this.update = this.update.bind(this)
    }

    update = async (newState: RxOutputState): Promise<void> => {
        this.element.innerHTML = newState // directly apply state as html
        this.state.next(newState)
    }
}

export {
    RxOutput
}