import 'whatwg-fetch' // used for Response typing
import { Subject } from 'rxjs'

import { ajax } from '../lib/common'
import { RxForm, RxSearchForm } from './form'

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

    it('can update its state', () => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rxf = new RxForm($form)
        const watcher = jest.fn()
        rxf.state.subscribe(watcher)
        rxf.update({ foo: 'bar' })
        expect(watcher).toHaveBeenCalledWith({ foo: 'bar' })
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
        </form>`
    })
    
    
    it('stores state as an observable sequence', () => {
        const $element = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($element)
        expect(rsf.state).toBeInstanceOf(Subject)
    })
    
    it('makes an async GET request to its endpoint on submission', done => {
        window.history.pushState({}, 'form', '/form') // to form a full request path
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(new Blob(['results!'], { type: 'text/plain' })) // a mock GET response
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        rsf.submit().then(() => { // check that we requested the right path, using the right header
            expect(window.fetch).toHaveBeenCalledWith('/form?query=mysearch', ajax)
            done()
        })
    })
    
    it('updates its state when it receives results', done => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(new Blob(['results!'], { type: 'text/plain' }))
        const watcher = jest.fn()
        rsf.state.subscribe(watcher)
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        rsf.submit().then(() => { // check that we pushed the new results onto state
            expect(watcher).toHaveBeenCalledWith({ results: 'results!' })
            done()
        })
    })
    
    it('updates the URL/browser history on submission', done => {
        const $form = document.querySelector('form') as HTMLFormElement
        const rsf = new RxSearchForm($form)
        const response = new Response(new Blob(['results!'], { type: 'text/plain' }))
        jest.spyOn(window, 'fetch').mockImplementation(() => Promise.resolve(response))
        rsf.submit().then(() => {
            expect(window.location.search).toBe('?query=mysearch') // querystring was changed
            expect(window.history.length).toBeGreaterThan(1) // we added entries to browser history
            done()
        })
    })

})