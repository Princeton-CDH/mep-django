import { Subject } from 'rxjs'

/**
 * Denotes a class that will keep a record of state changes as an observable
 * sequence, and allow that state to be updated externally.
 * 
 * We expect that the update() method will add the new state to the sequence,
 * as well as perform all changes necessary to reflect the new state.
 *
 * @interface Reactive
 * @template State
 */
interface Reactive<State> {
    state: Subject<State>
    update(state: Partial<State>): Promise<any>
}

/**
 * Base class that keeps a reference to an HTMLElement.
 *
 * @class Component
 */
class Component {
    element: HTMLElement

    constructor(element: HTMLElement) {
        this.element = element
    }
}

/**
 * Request header used to signal an ajax request to Django.
 */
const ajax = {
    headers: { 
        'X-Requested-With': 'XMLHttpRequest',
    }
}

/**
 * Validate that every element in array a is present in array b.
 *
 * @param {Array<any>} a
 * @param {Array<any>} b
 * @returns {boolean}
 */
function arraysAreEqual (a: Array<any>, b: Array<any>): boolean {
    return a.every(e => b.includes(e))
}

abstract class Rx<Element> {
    element: Element
    
    constructor(element: Element) {
        this.element = element
    }
}

export {
    Reactive,
    Component,
    Rx,
    ajax,
    arraysAreEqual
}