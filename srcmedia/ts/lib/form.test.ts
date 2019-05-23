import 'whatwg-fetch' // used for Response typing
import { Subject, Observable } from 'rxjs'

import { ajax } from '../lib/common'
import { RxForm, RxSearchForm, RxFacetedSearchForm } from './form'

describe('RxForm', () => {

    beforeEach(() => {
        document.body.innerHTML = `<form><input type="text" name="query"/></form>`
    })

    it('stores a target for submissions if one is set', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        $form.target = '/myendpoint/'
        const rxf = new RxForm($form)
        expect(rxf.target).toEqual('/myendpoint/')
    })
    
    it('uses the current page as target if none is set', () => {
        window.history.pushState({}, 'form', '/form/') // go to some path /form
        const $form = document.querySelector('form') as HTMLFormElement
        const rxf = new RxForm($form)
        expect(rxf.target).toEqual('/form/') // endpoint should be the path we're on
    })

    it('can reset itself', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const $input = document.querySelector('input[type=text]') as HTMLInputElement
        const rxf = new RxForm($form)
        $input.value = 'my search'
        rxf.reset()
        expect($input.value).toBe('')
    })
    
    it('can seralize itself', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const $input = document.querySelector('input[type=text]') as HTMLInputElement
        const rxf = new RxForm($form)
        $input.value = 'my search'
        expect(rxf.serialize()).toEqual('query=my+search')
    })

    it('ignores the enter key when pressed', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rxf = new RxForm($form)
        const enterPress = new KeyboardEvent('keydown', { key: 'Enter' })
        enterPress.preventDefault = jest.fn() // mock the preventDefault() hook
        $form.dispatchEvent(enterPress)
        expect(enterPress.preventDefault).toHaveBeenCalled()
    })

})

describe('RxSearchForm', () => {

    beforeEach(() => {
        document.body.innerHTML = `
        <form id="search">
            <input type="text" name="query" value="mysearch">
            <input type="number" name="age">
        </form>`
    })
    
    
    it('stores results as an observable sequence', () => {
        const $element = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($element)
        expect(rsf.results).toBeInstanceOf(Subject)
    })

    it('stores total results as an observable sequence', () => {
        const $element = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($element)
        expect(rsf.totalResults).toBeInstanceOf(Subject)
    })

    it('stores page labels as an observable sequence', () => {
        const $element = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($element)
        expect(rsf.pageLabels).toBeInstanceOf(Subject)
    })

    it('stores validity as an observable sequence', () => {
        const $element = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($element)
        expect(rsf.valid).toBeInstanceOf(Observable)
    })
    
    it('makes an async GET request to its endpoint on submission', () => {
        window.history.pushState({}, 'form', '/form') // to form a full request path
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(new Blob(['results!'], { type: 'text/plain' })) // a mock GET response
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        return rsf.getResults().then(() => { // check that we requested the right path, using the right header
            expect(window.fetch).toHaveBeenCalledWith('/form?query=mysearch', ajax)
        })
    })
    
    it('updates the results when it receives results', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(new Blob(['results!'], { type: 'text/plain' }))
        const watcher = jest.fn()
        rsf.results.subscribe(watcher)
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        return rsf.getResults().then(() => { // check that we pushed the new results onto state
            expect(watcher).toHaveBeenCalledWith('results!')
        })
    })

    it('updates the total results when it receives the correct header', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(
            new Blob(['results!'], { type: 'text/plain' }),
            { headers: { 'X-Total-Results': '50' } }
        )
        const watcher = jest.fn()
        rsf.totalResults.subscribe(watcher)
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        return rsf.getResults().then(() => {
            expect(watcher).toHaveBeenCalledWith('50')
        }) 
    })


    it('defaults to zero results if it doesn\'t receive the correct header', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(
            new Blob(['results!'], { type: 'text/plain' }), // no headers
        )
        const watcher = jest.fn()
        rsf.totalResults.subscribe(watcher)
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        return rsf.getResults().then(() => {
            expect(watcher).toHaveBeenCalledWith('0')
        }) 
    })

    it('parses and updates the page labels when it receives the correct header', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(
            new Blob(['results!'], { type: 'text/plain' }),
            { headers: { 'X-Page-Labels': 'page one|page two|page three' } } // will be split on '|'
        )
        const watcher = jest.fn()
        rsf.pageLabels.subscribe(watcher)
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        return rsf.getResults().then(() => {
            expect(watcher).toHaveBeenCalledWith(['page one', 'page two', 'page three'])
        }) 
    })

    it('defaults to empty page labels if it doesn\'t receive the correct header', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(
            new Blob(['results!'], { type: 'text/plain' }),
        )
        const watcher = jest.fn()
        rsf.pageLabels.subscribe(watcher)
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        return rsf.getResults().then(() => {
            expect(watcher).toHaveBeenCalledWith([''])
        }) 
    })
    
    it('updates the URL/browser history on submission', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(new Blob(['results!'], { type: 'text/plain' }))
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        return rsf.getResults().then(() => {
            expect(window.location.search).toBe('?query=mysearch') // querystring was changed
            expect(window.history.length).toBeGreaterThan(1) // we added entries to browser history
        })
    })

    it('updates its validity state when new results are received', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        rsf.valid.subscribe(valid => expect(valid).toBe(true))
        rsf.results.next('results!')
    })
})

describe('RxFacetedSearchForm', () => {

    beforeEach(() => {
        document.body.innerHTML = `
        <form id="search">
            <input type="text" name="query" value="mysearch">
        </form>`
    })

    it('stores facet data from solr as an observable sequence', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rfsf = new RxFacetedSearchForm($form)
        expect(rfsf.facets).toBeInstanceOf(Subject)
    })

    it('updates facet data when getFacets() is called', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rfsf = new RxFacetedSearchForm($form)
        const facets = {
            facet_fields: { 'facet_a': 'foo' },
            facet_heatmaps: {},
            facet_intervals: {},
            facet_queries: {},
            facet_ranges: {}
        }
        const response = new Response(new Blob([JSON.stringify(facets)], { type: 'application/json' }))
        const watcher = jest.fn()
        rfsf.facets.subscribe(watcher)
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        return rfsf.getFacets().then(() => {
            expect(watcher).toHaveBeenCalledWith(facets)
        })
    })

})