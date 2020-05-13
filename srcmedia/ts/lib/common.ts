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
 * Request header used to request facets from Django.
 */
const acceptJson = {
    headers: {
        'Accept': 'application/json'
    }
}

/**
 * Validate that every element in array a is present in array b and that
 * their lengths are the same.
 *
 * Will return false if elements are arrays, and ignores order.
 *
 * @param {Array<any>} a
 * @param {Array<any>} b
 * @returns {boolean}
 */
function arraysAreEqual (a: Array<any>, b: Array<any>): boolean {
    return a.every(e => b.includes(e)) && a.length == b.length
}

/**
 * Applies the 'aria-busy' attribute for the element's specified transition
 * duration, then changes its content and removes the attribute.
 *
 * @param {HTMLElement} element
 * @param {string} content
 * @returns {Promise<string>}
 */
function animateElementContent (element: HTMLElement, content: string): Promise<string> {
    return new Promise(resolve => {
        element.setAttribute('aria-busy', '')
        setTimeout(() => {
            element.innerHTML = content
            element.removeAttribute('aria-busy')
            resolve(content)
        }, getTransitionDuration(element))
    })
}

/**
 * Get the specified transition-duration for an element, or zero if none.
 *
 * Parses values from CSS like '0.5s' or '200ms' into an integer number of
 * milliseconds for use with functions like setTimeout().
 *
 * Note that this only works for elements that specify a single transition-duration
 * property.
 *
 * @param {HTMLElement} element
 * @returns {number}
 */
function getTransitionDuration (element: HTMLElement): number {
    const prop = window.getComputedStyle(element).getPropertyValue('transition-duration')
    const parsed = parseFloat(prop) * (/\ds$/.test(prop) ? 1000 : 1)
    return isNaN(parsed) ? 0 : parsed
}

abstract class Rx<E extends HTMLElement> {
    protected element: E

    constructor(element: E) {
        this.element = element
    }
}

/**
 * Utility function for faking a value change event on <input>s in tests.
 *
 * @param $element
 * @param value
 */
function fakeValueChange ($element: HTMLInputElement, value: string) {
    $element.value = value
    $element.dispatchEvent(new Event('input', { bubbles: true }))
}

/**
 * Utility function for faking a checkbox toggle event in tests.
 *
 * @param $element
 */
function fakeToggle ($element: HTMLInputElement) {
    $element.checked = !$element.checked
    $element.dispatchEvent(new Event('change'))
}

/**
 * Switch $element's aria-selected state, and if becomes true, set aria-selected
 * to false for every element in $others.
 *
 * If $element has aria-disabled set, do nothing.
 *
 * @param $element tab to activate
 * @param $others  list of other tabs to deactivate
 */
function toggleTab($element: HTMLElement, $others: HTMLElement[]) {
    if (!$element.hasAttribute('aria-disabled')) {
        if ($element.getAttribute('aria-selected') == 'true') {
            $element.setAttribute('aria-selected', 'false')
        }
        else {
            $element.setAttribute('aria-selected', 'true')
            $others.forEach($e => $e.setAttribute('aria-selected', 'false'))
        }
    }
}

/*
 * Adds a suffix that can be used to pluralize a string based on its argument.
 * Mimics Django's `pluralize` by accepting a number, string, or array, see:
 * https://docs.djangoproject.com/en/2.2/ref/templates/builtins/#pluralize
 *
 * @param n item to be pluralized
 */
function pluralize (n: number|string|Array<any>) {
    switch(typeof n) {
        case 'number': return n === 1 ? '' : 's'
        case 'string': return n === '1' ? '' : 's'
        case 'object': return n.length == 1 ? '' : 's'
    }
}

/**
 * Set the height of a set of sibling elements by traversing sibling pointers
 * recursively until all siblings have been reached.
 *
 * @param $element first sibling to set height of
 * @param height height in '50px' style string format
 */
function setAllHeights($element: HTMLElement, height: string) {
    $element.style.height = height
    if ($element.nextElementSibling) {
        setAllHeights(($element.nextElementSibling as HTMLElement), height)
    }
}

/**
 * Reverse a slugify-like operation, decoding a string like one_two_three to one
 * like "One Two Three".
 *
 * @param str string to operate on
 */
function unslugify(str: string) {
    return str.split('_')
              .map(part => part.charAt(0).toUpperCase() + part.substr(1))
              .join(' ')
}

export {
    Reactive,
    Component,
    Rx,
    ajax,
    acceptJson,
    arraysAreEqual,
    animateElementContent,
    getTransitionDuration,
    fakeValueChange,
    fakeToggle,
    toggleTab,
    pluralize,
    setAllHeights,
    unslugify
}