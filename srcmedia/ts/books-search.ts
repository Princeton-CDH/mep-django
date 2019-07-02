import { merge } from 'rxjs'
import { map, filter, mapTo, startWith, distinctUntilChanged, withLatestFrom, debounceTime } from 'rxjs/operators'

import PageControls from './components/PageControls'
import { RxSelect } from './lib/select'
import { RxOutput } from './lib/output'
import { RxFacetedSearchForm } from './lib/form'
import { arraysAreEqual } from './lib/common'

document.addEventListener('DOMContentLoaded', () => {

    /* ELEMENTS */
    const $booksSearchForm = document.getElementById('books-form') as HTMLFormElement
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement
    const $pageSelect = document.querySelector('select[name=page]') as HTMLSelectElement
    const $sortSelect = document.querySelector('select[name=sort]') as HTMLSelectElement
    const $resultsOutput = document.querySelector('output.results') as HTMLOutputElement
    const $totalResultsOutput = document.querySelector('output.total-results') as HTMLOutputElement
    const $errors = document.querySelector('div[role=alert].errors')

    /* COMPONENTS */
    const booksSearchForm = new RxFacetedSearchForm($booksSearchForm)
    const pageControls = new PageControls($pageControls)
    const pageSelect = new RxSelect($pageSelect)
    const sortSelect = new RxSelect($sortSelect)
    const resultsOutput = new RxOutput($resultsOutput)
    const totalResultsOutput = new RxOutput($totalResultsOutput)

    /* OBSERVABLES */
    const currentPage$ = pageSelect.value.pipe(
        startWith(pageSelect.element.value), // start with the current page
        map(p => parseInt(p)), // get a number from a string, for math
        distinctUntilChanged() // only update when changed
    )
    const totalResults$ = booksSearchForm.totalResults.pipe(
        map(t => parseInt(t)),
    )
    const totalPages$ = booksSearchForm.pageLabels.pipe(
        map(l => l.length), // number of page labels tells us the number of pages
        distinctUntilChanged()
    )
    const noResults$ = booksSearchForm.totalResults.pipe(
        map(t => t === '0'), // true if totalResults is '0'
        distinctUntilChanged()
    )
    const pageLabels$ = booksSearchForm.pageLabels.pipe(
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
    const reloadResults$ = merge( // a list of all the things that require fetching new results (jump to page 1)
        // reloadFacets$, // anything that changes facets also triggers new results
        sortSelect.value
    ).pipe(debounceTime(100))
    const totalResultsText$ = merge(
        totalResults$.pipe(map(t => `${t.toLocaleString()} total results`)), // when there are results, say how many, with a comma
        reloadResults$.pipe(mapTo('Results are loading')) // when loading, replace with this text
    )

    /* SUBSCRIPTIONS */

    // If there were errors, make sure they're cleared when the form becomes valid
    if ($errors) {
        booksSearchForm.valid.pipe(filter(v => v)).subscribe(() => {
            $errors.remove() // NOTE could use a nicer animation here?
        })
    }

    // Disable the page selection dropdown if there aren't any results
    noResults$.subscribe(pageSelect.disabled)

    // When we need new results, go back to page 1
    reloadResults$.subscribe(() => pageSelect.value.next('1'))

    // When the page is changed, submit the form and apply loading styles
    pageSelect.value.subscribe(() => {
        booksSearchForm.getResults()
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
    booksSearchForm.results.pipe(
        withLatestFrom(currentPage$, totalPages$)
    ).subscribe(([results, currentPage, totalPages]) => {
        pageControls.update([currentPage, totalPages])
        pageControls.element.removeAttribute('aria-busy')
        resultsOutput.element.removeAttribute('aria-busy')
        resultsOutput.update(results)
    })
})
