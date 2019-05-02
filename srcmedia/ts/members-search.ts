import { merge } from 'rxjs'
import { pluck, map, withLatestFrom, startWith, distinctUntilChanged, mapTo, filter } from 'rxjs/operators'

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

    /* OBSERVABLES */
    const currentPage$ = pageSelect.value.pipe(
        startWith(pageSelect.element.value), // start with the current page
        map(p => parseInt(p)), // get a number from a string, for math
        distinctUntilChanged() // only update when changed
    )
    const totalResults$ = membersSearchForm.totalResults.pipe(
        map(t => parseInt(t)),
        distinctUntilChanged()
    )
    const totalPages$ = membersSearchForm.pageLabels.pipe(
        map(l => l.length), // number of page labels tells us the number of pages
        distinctUntilChanged()
    )
    const noResults$ = membersSearchForm.totalResults.pipe(
        map(t => t === '0'), // true if totalResults is '0'
        distinctUntilChanged()
    )
    const noKeyword$ = keywordInput.state.pipe(
        pluck('value'),
        map(v => v === ''), // true if the value of the keyword input is ''
        distinctUntilChanged()
    )
    const pageLabels$ = membersSearchForm.pageLabels.pipe(
        startWith([...Array(pageSelect.element.options.length)].map((_, i) => {
            return pageSelect.element.options[i].innerHTML // compare with the initial page labels
        })),
        distinctUntilChanged(arraysAreEqual),
        filter(l => !arraysAreEqual(l, [""])) // ignore empty page labels
    )
    const noResultsPageOption$ = noResults$.pipe(
        filter(n => n === true), // only generate if no results
        mapTo([{ value: '1', text: 'N/A' }]) // create a 'N/A' page option    
    )
    const pageLabelOptions$ = merge(
        pageLabels$.pipe( // generate new <options> based on page labels if we have any
            map(labels => labels.map((label, pageNumber) => ({
                value: (pageNumber + 1).toString(), // <option> value is its index (page number)
                text: label, // text is the page label
            })))
        ),
        noResultsPageOption$ // if no results, use the 'N/A' label
    )
    const nextPage$ = pageControls.pageChanges.pipe(
        withLatestFrom(currentPage$), // check the current page
        map(([a, c]) => a === 'next' ? c + 1 : c - 1), // if 'next', add 1, otherwise subtract 1
        map(c => c.toString()) // map to a string for passing as pageSelect value
    )
    const reloadResults$ = merge( // a list of all the things that should submit the form when changed
        keywordInput.state,
        hasCardInput.state,
        sortSelect.value
    )
    const totalResultsText$ = merge(
        totalResults$.pipe(map(t => `${t} total results`)), // when there are results, say how many 
        reloadResults$.pipe(mapTo('Results are loading')) // when loading, replace with this text
    )
    const sort$ = noKeyword$.pipe( // 'name' if no keyword, 'relevance' otherwise
        map(n => n ? 'name' : 'relevance')
    )

    /* SUBSCRIPTIONS */

    // Change the sort depending on if a keyword is active or not
    sort$.subscribe(sortSelect.value)

    // Disable the page selection dropdown if there aren't any results
    noResults$.subscribe(pageSelect.disabled)

    // When a user changes the search or sort, go back to page 1
    reloadResults$.subscribe(() => pageSelect.value.next('1'))

    // When the page is changed, submit the form and apply loading styles
    pageSelect.value.subscribe(() => {
        membersSearchForm.submit()
        pageControls.element.setAttribute('aria-busy', '') // empty string used for boolean attributes
        resultsOutput.element.setAttribute('aria-busy', '') 
    })

    // When next/previous page links are clicked, go to the next page
    nextPage$.subscribe(pageSelect.value)

    // When the page labels change, pass them to the page select to re-render options
    pageLabelOptions$.subscribe(pageSelect.options)

    // Keep the "total results" text updated
    totalResultsText$.subscribe(totalResultsOutput.update)

    // When results are loaded, remove loading styles and display the results
    // Also update the next/prev buttons in case they become disabled
    membersSearchForm.results.pipe(
        withLatestFrom(currentPage$, totalPages$)
    ).subscribe(([results, currentPage, totalPages]) => {
        pageControls.update([currentPage, totalPages])
        pageControls.element.removeAttribute('aria-busy')
        resultsOutput.element.removeAttribute('aria-busy')
        resultsOutput.update(results)
    })
})
