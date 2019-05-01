import { Subject } from 'rxjs'

import { Component, ajax, acceptJson } from './common'

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
     * NOTE TypeScript isn't aware FormData can be passed directly to
     * URLSearchParams(), hence the ignore. Open issue:
     * https://github.com/Microsoft/TypeScript/issues/30584#issuecomment-486967902
     *
     * @returns {string}
     * @memberof ReactiveForm
     */
    serialize = (): string => {
        // @ts-ignore
        return new URLSearchParams(new FormData(this.element)).toString()
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
    pageLabels: Subject<Array<string>>
    facets: Subject<object>

    constructor(element: HTMLFormElement) {
        super(element)
        this.results = new Subject()
        this.totalResults = new Subject()
        this.pageLabels = new Subject()
    }
    /**
     * Serialize the form and submit it as a GET request to the form's endpoint,
     * passing the response to update().
     * 
     * Also updates the browser history, saving the search.
     *
     * @returns {Promise<any>}
     * @memberof PageSearchForm
     */
    submit = async (): Promise<any> => {
        this.element.toggleAttribute('aria-busy') // set the busy state
        const serialized = this.serialize() // serialize the form for later
        return fetch(`${this.target}?${serialized}`, ajax)
            .then(res => {
                const totalResults = res.headers.get('X-Total-Results')
                const pageLabels = res.headers.get('X-Page-Labels')
                if (totalResults) this.totalResults.next(totalResults)
                if (pageLabels) this.pageLabels.next(pageLabels.split('|'))
                return res.text()
            })
            .then(results => {
                this.results.next(results)
                this.element.toggleAttribute('aria-busy')
                window.history.pushState(null, document.title, `?${serialized}`)
        })
    }
    getResults = async (formData: string): Promise<void> => {
        fetch(`${this.target}?${formData}`, ajax).then()
    }
    getFacets = async (formData: string): Promise<void> => {
        return fetch(`${this.target}?${formData}`, acceptJson)
            .then(res => res.json())
            .then(facets => this.facets.next(facets))
    }
}

export {
    RxForm,
    RxSearchForm,
}