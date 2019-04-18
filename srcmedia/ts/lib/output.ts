import { Subject } from 'rxjs'

import { Component, Reactive } from '../lib/common'

// State represented as just a string for now, e.g. for html responses
type RxOutputState = string

class RxOutput extends Component implements Reactive<RxOutputState> {
    state: Subject<RxOutputState>

    constructor(element: HTMLOutputElement) {
        super(element)
        this.state = new Subject()
        this.update = this.update.bind(this)
    }

    async update(newState: RxOutputState): Promise<void> {
        this.element.innerHTML = newState // directly apply state as html
        this.state.next(newState)
    }
}

export {
    RxOutput
}