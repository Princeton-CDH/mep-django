import { Subject } from 'rxjs'

import { Component, ajax } from './common'

class RxForm extends Component {
    element: HTMLFormElement
    target: string

    constructor(element: HTMLFormElement) {
        super(element)
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

class RxSearchForm extends RxForm {
    results: Subject<string>
    totalResults: Subject<string>

    constructor(element: HTMLFormElement) {
        super(element)
        this.results = new Subject()
        this.totalResults = new Subject()
    }
    /**
     * Serialize the form and submit it as a GET request to the form's endpoint,
     * passing the response to update().
     * 
     * Also updates the browser history, saving the search.
     *
     * @returns {AsyncSubject<any>}
     * @memberof PageSearchForm
     */
    submit = async (): Promise<any> => {
        this.element.toggleAttribute('aria-busy') // set the busy state
        const serialized = this.serialize() // serialize the form for later
        return fetch(`${this.target}?${serialized}`, ajax)
            .then(res => {
                const totalResults = res.headers.get('X-Total-Results')
                if (totalResults) this.totalResults.next(totalResults)
                return res.text()
            })
            .then(results => {
                this.results.next(results)
                this.element.toggleAttribute('aria-busy')
                window.history.pushState(null, document.title, `?${serialized}`)
        })
    }
}

export {
    RxForm,
    RxSearchForm,
}