import { Subject } from 'rxjs'

import { Reactive, Component, ajax } from './common'

interface RxFormState {
    // eventually this could include generic things like validity
}

class RxForm extends Component implements Reactive<RxFormState> {
    element: HTMLFormElement
    state: Subject<RxFormState>
    target: string

    constructor(element: HTMLFormElement) {
        super(element)
        this.state = new Subject()
        if (this.element.target) { // check for a `target` attribute
            this.target = this.element.target
        }
        else { // otherwise assume it targets the current path
            this.target = window.location.pathname
        }
        // prevent the enter key from submitting the form
        this.element.onkeydown = e => { if (e.key === 'Enter') e.preventDefault() }
    }
    /**
     * Update the form's state. We don't need to change the DOM, so all we do
     * is call next().
     *
     * @param {RxFormState} state
     * @returns {Promise<void>}
     * @memberof RxForm
     */
    update = async (state: RxFormState): Promise<void> => {
        this.state.next(state)
    }
    /**
     * Serializes the form's state for appending to a URL querystring.
     *
     * @returns {string}
     * @memberof ReactiveForm
     */
    serialize = (): string => {
        let data = new FormData(this.element)
        let output: { [key: string]: any } = {}
        for (let pair of data.entries()) {
            output[pair[0]] = pair[1]
        }
        return new URLSearchParams(output).toString()
    }
    /**
     * Resets the form to its initial state by calling the native reset() hook.
     *
     * @returns {void}
     * @memberof ReactiveForm
     */
    reset = (): void => {
        return this.element.reset()
    }
}

interface RxSearchFormState extends RxFormState {
    results: string
}

class RxSearchForm extends RxForm implements Reactive<RxSearchFormState> {
    state: Subject<RxSearchFormState>
    
    constructor(element: HTMLFormElement) {
        super(element)
    }
    /**
     * Serialize the form and submit it as a GET request to the form's endpoint,
     * passing the response to update().
     * 
     * Also updates the browser history, saving the search.
     *
     * @returns {Promise<void>}
     * @memberof PageSearchForm
     */
    submit = async (): Promise<void> => {
        return fetch(`${this.target}?${this.serialize()}`, ajax)
            .then(res => res.text())
            .then(html => this.update({ results: html }))
            .then(() => window.history.pushState(null, document.title, `?${this.serialize()}`))
    }
}

export {
    RxForm,
    RxFormState,
    RxSearchForm,
    RxSearchFormState,
}