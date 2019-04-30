import { merge, partition } from 'rxjs'
import { pluck, map, withLatestFrom, startWith, distinctUntilChanged } from 'rxjs/operators'

import { arraysAreEqual } from './lib/common'
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

    // When a keyword search is active, switch to relevance
    // Otherwise switch to name
    // partition() is like filter() but creates two observables: those that
    // fulfill the condition and those that don't
    const [keywordOn, keywordOff] = partition(
        keywordInput.state.pipe(pluck('value')), value => value === '')
    keywordOn.subscribe(() => sortSelect.value.next('name'))
    keywordOff.subscribe(() => sortSelect.value.next('relevance'))

    // When a user changes the search or sort, go back to page 1
    merge(
        keywordInput.state,
        hasCardInput.state,
        sortSelect.value,
    ).subscribe(() => {
        pageSelect.value.next('1')
        totalResultsOutput.update('Results are loading')
    })

    // When the page is changed, submit the form and apply loading styles
    pageSelect.value.subscribe(() => {
        membersSearchForm.submit()
        pageControls.element.setAttribute('aria-busy', '') // empty string used for boolean attributes
        resultsOutput.element.setAttribute('aria-busy', '') 
    })

    // When next/previous page links are clicked, go to that page
    pageControls.pageChanges.pipe( // for every next/prev click
        withLatestFrom(pageSelect.value.pipe( // get the current page
            startWith(pageSelect.element.value), // start with the one it's currently on
            map(pageNumber => parseInt(pageNumber)) // parse into an integer
        )),
    // ).pipe( // withLatestFrom will return an array of the two observables we merged
        map(([action, currentPage]) => { // if next, add 1, otherwise subtract 1
            return (action === 'next' ? currentPage + 1 : currentPage - 1)
        }), // create a { value: nextPage } object to pass back to the <select>
        map(nextPageNumber => nextPageNumber.toString())
    ).subscribe(pageSelect.value) // update the <select> as though we chose that page
    
    // When the page changes, update the page controls in case next/prev become disabled
    pageSelect.value.pipe(
        startWith(pageSelect.element.value),
        map(pageNumber => parseInt(pageNumber)), // get the current page number, as above
        map(pageNumber => [pageNumber, pageSelect.element.length]) // append the total number of pages
    ).subscribe(pageControls.update)

    // When the page labels change, pass them to the page select to re-render options
    membersSearchForm.pageLabels.pipe(
        startWith([...Array(pageSelect.element.options.length)].map((_, i) => {
            return pageSelect.element.options[i].innerHTML // compare with the initial page labels
        })),
        distinctUntilChanged(arraysAreEqual), // don't do anything if the page labels didn't change
        map(labels => {
            return labels.map((label, pageNumber) => ({
                value: (pageNumber + 1).toString(), // <option> value is its index (page number)
                text: label, // text is the page label
            }))
        })
    ).subscribe(pageSelect.options)

    // When the number of total results changes, display it
    membersSearchForm.totalResults.pipe(
        distinctUntilChanged(),
        map(total => `${total} total results`)
    ).subscribe(totalResultsOutput.update)

    // When results are loaded, remove loading styles and display the results
    membersSearchForm.results.subscribe(results => {
        pageControls.element.removeAttribute('aria-busy')
        resultsOutput.element.removeAttribute('aria-busy')
        resultsOutput.update(results)
    })
})
