import { Subject } from 'rxjs'

import { RxCheckboxInput } from './input'
import { animateElementContent } from './common'

class RxBooleanFacet extends RxCheckboxInput {
    count: Subject<number>
    countElement: HTMLElement | null

    constructor(element: HTMLInputElement) {
        super(element)
        this.count = new Subject()
        if (this.label) this.countElement = this.label.querySelector('.count')
        this.count.subscribe(this.updateCount)
    }

    protected updateCount = async (count: number): Promise<string> => {
        return animateElementContent(this.element, count.toString())
    }
}

export {
    RxBooleanFacet,
}