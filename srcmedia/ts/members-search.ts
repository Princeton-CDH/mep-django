import { merge, combineLatest } from 'rxjs'
import { pluck, map, withLatestFrom, startWith } from 'rxjs/operators'

import { RxTextInput, RxCheckboxInput } from './lib/input'
import { RxOutput } from './lib/output'
import { RxSearchForm } from './lib/form'
import { RxSelect } from './lib/select'
import PageControls from './components/PageControls'

document.addEventListener('DOMContentLoaded', () => {

    /* ELEMENTS */
    const $membersSearchForm = document.getElementById('members-form') as HTMLFormElement
    const $keywordInput = document.querySelector('input[name=query]') as HTMLInputElement
    const $hasCardInput = document.querySelector('input[name=has_card]') as HTMLInputElement
    const $resultsOutput = document.querySelector('output[form=members-form]') as HTMLOutputElement
    const $totalResultsOutput = document.querySelector('output.total-results') as HTMLOutputElement
    const $pageSelect = document.querySelector('select[name=page]') as HTMLSelectElement
    const $sortSelect = document.querySelector('select[name=sort]') as HTMLSelectElement
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement
    const $nextPageLink = document.querySelector('.sort-pages a[rel=next]') as HTMLAnchorElement
    const $prevPageLink = document.querySelector('.sort-pages a[rel=prev]') as HTMLAnchorElement

    /* COMPONENTS */
    const membersSearchForm = new RxSearchForm($membersSearchForm)
    const keywordInput = new RxTextInput($keywordInput)
    const hasCardInput = new RxCheckboxInput($hasCardInput)
    const resultsOutput = new RxOutput($resultsOutput)
    const totalResultsOutput = new RxOutput($totalResultsOutput)
    const pageSelect = new RxSelect($pageSelect)
    const sortSelect = new RxSelect($sortSelect)
    const pageControls = new PageControls($pageControls)

    /* BINDINGS */
    // Form submission bindings
    merge(
        keywordInput.state,
        hasCardInput.state,
        pageSelect.state,
        sortSelect.state,
    ).subscribe(() => {
        membersSearchForm.submit()
        membersSearchForm.element.classList.add('loading') // add 'loading' classes
        resultsOutput.element.classList.add('loading')
        totalResultsOutput.element.innerHTML = 'Results are loading'
        resultsOutput.element.setAttribute('aria-busy', 'true') // indicate that results are loading via ARIA
    })

    // Next/Previous page control bindings
    pageControls.pageChanges.pipe( // for every next/prev click
        withLatestFrom(pageSelect.state.pipe( // get the current page
            pluck('value'), // which is the value of the <select>
            startWith($pageSelect.value), // start with the one it's currently on
            map(pageNumber => parseInt(pageNumber)) // parse into an integer
        ))
    ).pipe( // withLatestFrom will return an array of the two observables we merged
        map(([action, currentPage]) => { // if next, add 1, otherwise subtract 1
            return (action === 'next' ? currentPage + 1 : currentPage - 1)
        }), // create a { value: nextPage } object to pass back to the <select>
        map(nextPageNumber => ({ value: nextPageNumber.toString() }))
    ).subscribe(pageSelect.update) // update the <select> as though we chose that page

    // Form update bindings
    membersSearchForm.state.pipe(pluck('results')).subscribe(results => {
        membersSearchForm.element.classList.remove('loading') // remove 'loading' classes
        resultsOutput.element.classList.remove('loading')
        totalResultsOutput.element.innerHTML = 'Results have loaded'
        resultsOutput.element.removeAttribute('aria-busy')
        resultsOutput.update(results) // pass updated results to the output
    })
})
