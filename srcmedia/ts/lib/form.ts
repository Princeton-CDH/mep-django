import { Subject, pipe, Observable } from 'rxjs'
import { distinctUntilChanged } from 'rxjs/operators'

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

/**
 * An RxForm that includes methods for requesting and paging through search
 * results, which it stores as observable sequences.
 *
 * @class RxSearchForm
 * @extends {RxForm}
 */
class RxSearchForm extends RxForm {
    // Observables
    results: Subject<string>
    totalResults: Subject<string>
    pageLabels: Subject<Array<string>>
    // Readonly constants
    protected readonly TOTAL_RESULTS_HEADER: string = 'X-Total-Results'
    protected readonly PAGE_LABELS_HEADER: string = 'X-Page-Labels'  
    protected readonly PAGE_LABELS_SEPARATOR: string = '|'

    constructor(element: HTMLFormElement) {
        super(element)
        this.results = new Subject()
        this.totalResults = new Subject()
        this.pageLabels = new Subject()
    }

    /**
     * Make an ajax request for result data, and use it to:
     * - update the total result count
     * - update the page labels
     * - update the results observable
     * - update the URL querystring
     *
     * @memberof RxSearchForm
     */
    getResults = async (): Promise<Response> => {
        return this.fetchResults(this.serialize())
            .then(this.updateTotalResults)
            .then(this.updatePageLabels)
            .then(this.updateResults)
            .then(this.updateQueryString)
    }
    /**
     * Make an ajax request for result data.
     *
     * @protected
     * @memberof RxSearchForm
     */
    protected fetchResults = async (formData: string): Promise<Response> => {
        return fetch(`${this.target}?${formData}`, ajax)
    }
    /**
     * If the response contained valid non-empty result data as HTML,
     * add it as the next value in the result observable stream.
     *
     * @protected
     * @memberof RxSearchForm
     */
    protected updateResults = async (res: Response): Promise<Response> => {
        const results: string = await res.text()
        if (results) this.results.next(results)
        return res
    }
    /**
     * If the response sent the configured TOTAL_RESULT_HEADER, get its value
     * and set it as the next value in the total results observable stream.
     *
     * @protected
     * @memberof RxSearchForm
     */
    protected updateTotalResults = async (res: Response): Promise<Response> => {
        const totalResults = res.headers.get(this.TOTAL_RESULTS_HEADER) || '0'
        this.totalResults.next(totalResults)
        return res
    }
    /**
     * If the response sent the configured PAGE_LABELS_HEADER, get its value
     * and set it as the next value in the page labels observable stream.
     *
     * @protected
     * @memberof RxSearchForm
     */
    protected updatePageLabels = async (res: Response): Promise<Response> => {
        const pageLabels = res.headers.get(this.PAGE_LABELS_HEADER) || ''
        this.pageLabels.next(pageLabels.split(this.PAGE_LABELS_SEPARATOR))
        return res
    }
    /**
     * Update the browser's querystring and history based on the current state
     * of the form. Passes on the provided response unchanged for convenience.
     *
     * @protected
     * @memberof RxSearchForm
     */
    protected updateQueryString = async (res: Response): Promise<Response> => {
        window.history.pushState(null, document.title, `?${this.serialize()}`)
        return res
    }
}

interface SolrFacets {
    facet_fields: object,
    facet_heatmaps: object,
    facet_intervals: object,
    facet_queries: object,
    facet_ranges: object
}

/**
 * An RxSearchForm that includes methods for requesting and updating facet data
 * returned as JSON from Apache solr, which it stores as an observable.
 *
 * @class RxFacetedSearchForm
 * @extends {RxSearchForm}
 */
class RxFacetedSearchForm extends RxSearchForm {
    facets: Subject<SolrFacets>

    constructor(element: HTMLFormElement) {
        super(element)
        this.facets = new Subject()
    }
    /**
     * Make an ajax request for facet data and use it to update the facets
     * observable.
     *
     * @memberof RxSearchForm
     */
    getFacets = async (): Promise<Response> => {
        return this.fetchFacets(this.serialize()).then(this.updateFacets)
    }
    /**
     * Make an ajax request for facet data.
     *
     * @protected
     * @memberof RxSearchForm
     */
    protected fetchFacets = async (formData: string): Promise<Response> => {
        return fetch(`${this.target}?${formData}`, acceptJson)
    }
    /**
     * If the response contained valid non-empty facet data as JSON,
     * add it as the next value in the facet observable stream.
     *
     * @protected
     * @memberof RxSearchForm
     */
    protected updateFacets = async (res: Response): Promise<Response> => {
        const facets: SolrFacets = await res.json()
        if (facets) this.facets.next(facets)
        return res
    }
}

export {
    RxForm,
    RxSearchForm,
    RxFacetedSearchForm,
    SolrFacets
}