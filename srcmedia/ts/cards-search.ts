import { merge } from 'rxjs'
import { pluck, map, withLatestFrom, startWith, distinctUntilChanged, mapTo, filter, debounceTime, flatMap, skip, tap } from 'rxjs/operators'

import { arraysAreEqual, pluralize } from './lib/common'
import { RxTextInput } from './lib/input'
import { RxOutput } from './lib/output'
import { RxFacetedSearchForm } from './lib/form'
import { RxSelect } from './lib/select'
import PageControls from './components/PageControls'

document.addEventListener('DOMContentLoaded', () => {

    /* ELEMENTS */
    const $cardsSearchForm = document.getElementById('cards-form') as HTMLFormElement
    const $resultsOutput = document.querySelector('output.results') as HTMLOutputElement
    const $totalResultsOutput = document.querySelector('output.total-results') as HTMLOutputElement
    const $pageSelect = document.querySelector('select[name=page]') as HTMLSelectElement
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement
    const $errors = document.querySelector('div[role=alert].errors')

    /* COMPONENTS */
    const cardsSearchForm = new RxFacetedSearchForm($cardsSearchForm)
    const resultsOutput = new RxOutput($resultsOutput)
    const totalResultsOutput = new RxOutput($totalResultsOutput)
    const pageSelect = new RxSelect($pageSelect)
    const pageControls = new PageControls($pageControls)

    /* OBSERVABLES */
    const currentPage$ = pageSelect.value.pipe(
        startWith(pageSelect.element.value), // start with the current page
        map(p => parseInt(p)), // get a number from a string, for math
        distinctUntilChanged() // only update when changed
    )
    const totalResults$ = cardsSearchForm.totalResults.pipe(
        map(t => parseInt(t)),
    )
    const totalPages$ = cardsSearchForm.pageLabels.pipe(
        map(l => l.length), // number of page labels tells us the number of pages
        distinctUntilChanged()
    )
    const noResults$ = cardsSearchForm.totalResults.pipe(
        map(t => t === '0'), // true if totalResults is '0'
        distinctUntilChanged()
    )
    const reloadResults$ = merge( // a list of all the things that require fetching new results (jump to page 1)
        // reloadFacets$, // anything that changes facets also triggers new results
        // sortSelect.value
    ).pipe(debounceTime(100))

    const nextPage$ = pageControls.pageChanges.pipe(
        withLatestFrom(currentPage$), // check the current page
        map(([a, c]) => a === 'next' ? c + 1 : c - 1), // if 'next', add 1, otherwise subtract 1
        map(c => c.toString()) // map to a string for passing as pageSelect value
    )
    const pageLabels$ = cardsSearchForm.pageLabels.pipe(
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
                text: label.replace('-', '–'), // text is the page label; replace hyphens with en dashes
            })))
        ),
        noResultsPageOption$ // if no results, use the 'N/A' label
    )
    /* SUBSCRIPTIONS */

    // If there were errors, make sure they're cleared when the form becomes valid
    if ($errors) {
        cardsSearchForm.valid.pipe(filter(v => v)).subscribe(() => {
            $errors.remove() // NOTE could use a nicer animation here?
        })
    }

    // Change the sort depending on if a keyword is active or not
    // sort$.subscribe(sortSelect.value)

    // Disable the page selection dropdown if there aren't any results
    noResults$.subscribe(pageSelect.disabled)

    // When a user changes the form, get new facets
    // reloadFacets$.subscribe(() => membersSearchForm.getFacets())

    // When we need new results, go back to page 1
    reloadResults$.subscribe(() => pageSelect.value.next('1'))

    // slight debounce - otherwise we would get repeated events when e.g.
    // the user types a keyword, which also switches the sort to relevance
    // debounce ensures these are close enough to read as a single event
    const totalResultsText$ = merge(
        totalResults$.pipe(map(t => `${t.toLocaleString()} total result${pluralize(t)}`)), // when there are results, say how many, with a comma
        reloadResults$.pipe(mapTo('Results are loading')) // when loading, replace with this text
    )

    // When the page is changed, submit the form and apply loading styles
    pageSelect.value.subscribe(() => {
        cardsSearchForm.getResults()
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
       cardsSearchForm.results.pipe(
        withLatestFrom(currentPage$, totalPages$)
    ).subscribe(([results, currentPage, totalPages]) => {
        pageControls.update([currentPage, totalPages])
        pageControls.element.removeAttribute('aria-busy')
        resultsOutput.element.removeAttribute('aria-busy')
        resultsOutput.update(results)
    })

})
