import { merge, partition, Observable } from 'rxjs'
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

    // Sort bindings
    const [keywordOn, keywordOff] = partition(
        keywordInput.state.pipe(pluck('value')), value => value === '')
    keywordOn.subscribe(() => sortSelect.update({ value: 'name' }))
    keywordOff.subscribe(() => sortSelect.update({ value: 'relevance' }))

    // When a user changes the search, go back to page 1
    merge(
        keywordInput.state,
        hasCardInput.state,
        sortSelect.state,
    ).subscribe(() => {
        pageSelect.update({ value: '1' })
    })

    // When the page is changed, submit the form and apply loading styles
    pageSelect.state.subscribe(() => {
        membersSearchForm.submit()
        resultsOutput.element.setAttribute('aria-busy', '') // empty string used for boolean attributes
        totalResultsOutput.update('Results are loading')
    })

    // When next/previous page links are clicked, go to that page
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
    
    pageSelect.state.pipe(
        pluck('value'), // which is the value of the <select>
        startWith($pageSelect.value), // start with the one it's currently on
        map(pageNumber => parseInt(pageNumber)), // parse into an integer
        map(pageNumber => [pageNumber, $pageSelect.length]) // append the total number of pages
    ).subscribe(pageControls.update)

    // When the number of total results changes, display it
    membersSearchForm.totalResults.pipe(
        map(total => `${total} total results`)
    ).subscribe(totalResultsOutput.update)

    // When results are loaded, remove loading styles and display the results
    membersSearchForm.results.subscribe(results => {
        resultsOutput.element.removeAttribute('aria-busy')
        resultsOutput.update(results)
    })
})
