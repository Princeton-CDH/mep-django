import { merge } from 'rxjs'
import { map, filter, mapTo, startWith, distinctUntilChanged, withLatestFrom, debounceTime, skip } from 'rxjs/operators'

import { RxSelect } from './lib/select'
import { RxOutput } from './lib/output'
import { RxFacetedSearchForm } from './lib/form'
import { RxTextInput } from './lib/input'
import { arraysAreEqual } from './lib/common'
import { RxRangeFilter, rangesAreEqual } from './lib/filter'
import ActiveFilters from "./components/ActiveFilters"
import PageControls from './components/PageControls'

document.addEventListener('DOMContentLoaded', () => {

    /* ELEMENTS */
    const $booksSearchForm = document.getElementById('books-form') as HTMLFormElement
    const $keywordInput = document.querySelector('input[name=query]') as HTMLInputElement
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement
    const $pageSelect = document.querySelector('select[name=page]') as HTMLSelectElement
    const $sortSelect = document.querySelector('select[name=sort]') as HTMLSelectElement
    const $relevanceSortOption = document.querySelector('select[name=sort] option[value="relevance"]') as HTMLElement
    const $resultsOutput = document.querySelector('output.results') as HTMLOutputElement
    const $totalResultsOutput = document.querySelector('output.total-results') as HTMLOutputElement
    const $errors = document.querySelector('div[role=alert].errors')
    const $circDateFacet = document.querySelector('#id_circulation_dates') as HTMLFieldSetElement
    const $activeFilters = document.querySelector('.active-filters') as HTMLDivElement
    const bottomOfForm = $booksSearchForm.getBoundingClientRect().bottom

    /* COMPONENTS */
    const booksSearchForm = new RxFacetedSearchForm($booksSearchForm)
    const keywordInput = new RxTextInput($keywordInput)
    const pageControls = new PageControls($pageControls)
    const pageSelect = new RxSelect($pageSelect)
    const sortSelect = new RxSelect($sortSelect)
    const resultsOutput = new RxOutput($resultsOutput)
    const totalResultsOutput = new RxOutput($totalResultsOutput)
    const circDateFacet = new RxRangeFilter($circDateFacet)
    const activeFilters = new ActiveFilters($activeFilters)

    /* OBSERVABLES */
    const currentPage$ = pageSelect.value.pipe(
        startWith(pageSelect.element.value), // start with the current page
        map(p => parseInt(p, 10)), // get a number from a string, for math
        distinctUntilChanged() // only update when changed
    )
    const totalResults$ = booksSearchForm.totalResults.pipe(
        map(t => parseInt(t, 10)),
    )
    const totalPages$ = booksSearchForm.pageLabels.pipe(
        map(l => l.length), // number of page labels tells us the number of pages
        distinctUntilChanged()
    )
    const noResults$ = booksSearchForm.totalResults.pipe(
        map(t => t === '0'), // true if totalResults is '0'
        distinctUntilChanged()
    )
    const keywordChange$ = keywordInput.value$.pipe( // debounced, deduped changes
        skip(1), // ignore initial value
        debounceTime(500),
        distinctUntilChanged()
    )
    const noKeyword$ = keywordInput.value$.pipe(
        map(v => v === ''), // true if the value of the keyword input is ''
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
                text: label.replace('-', '–'), // text is the page label; replace hyphens with en dashes
            })))
        ),
        noResultsPageOption$ // if no results, use the 'N/A' label
    )
    const nextPage$ = pageControls.pageChanges.pipe(
        withLatestFrom(currentPage$), // check the current page
        map(([a, c]) => a === 'next' ? c + 1 : c - 1), // if 'next', add 1, otherwise subtract 1
        map(c => c.toString()) // map to a string for passing as pageSelect value
    )
    const circDateChange$ = circDateFacet.value$.pipe( // debounced, deduped and valid changes
        debounceTime(500), // debounce
        withLatestFrom(circDateFacet.valid$), // check validity
        distinctUntilChanged(([a, aValid], [b, bValid]) => { // for the first entry (used only for comparison),
            return rangesAreEqual(a, b) && (aValid == bValid) // we care whether there was a change in validity OR values
        }),
        skip(1), // for all other entries (used to actually update)
        filter(([range, valid]) => valid), // only accept valid submissions
        map(([range, valid]) => range), // only need range
        distinctUntilChanged(rangesAreEqual) // ignore identical ranges, since we will always have valid ones
    )
    const reloadFacets$ = merge( // a list of all the things that require fetching new facets
        keywordChange$,
        circDateChange$,
    )
    const reloadResults$ = merge( // a list of all the things that require fetching new results (jump to page 1)
        reloadFacets$, // anything that changes facets also triggers new results
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

        // scroll up to put top in view, if needed
        const barHeight = $pageControls.getBoundingClientRect().height
        const listOffset = ($resultsOutput.getBoundingClientRect() as DOMRect).y
        if ((listOffset - barHeight) < 0) {
            window.scroll({ top: bottomOfForm, behavior: 'smooth' })
        }
    })

    // When next/previous page links are clicked, go to the next page
    nextPage$.subscribe(pageSelect.value)

    // When the page labels change, pass them to the page select to re-render options
    pageLabelOptions$.subscribe(pageSelect.options)

    // Keep the "total results" text updated
    totalResultsText$.subscribe(totalResultsOutput.update)

    // If the circulation date facet had an error, make sure it's cleared when it becomes valid
    if ($circDateFacet.classList.contains('error')) {
        circDateFacet.valid$.pipe(filter(v => v)).subscribe(() => {
            $circDateFacet.classList.remove('error')
        })
    }

    noKeyword$.subscribe((noKeyword) => {
        // disable relevance sort option if there is no keyword search
        const sortOptionsArray = Array.from($sortSelect.options)
        const sortSelectRelevanceIndex = sortOptionsArray.findIndex(opt => opt.value == 'relevance')
        const sortSelectTitleIndex = sortOptionsArray.findIndex(opt => opt.value == 'title')
        if (noKeyword) {
            // disable relevance sort option
            $relevanceSortOption.setAttribute('disabled', 'true')
            // if current sort is relevance, switch to title
            if ($sortSelect.selectedIndex == sortSelectRelevanceIndex) {
                $sortSelect.selectedIndex = sortSelectTitleIndex
            }
        } else {
            // un-disable relevance sort option and select it
            $relevanceSortOption.removeAttribute('disabled')
            $sortSelect.selectedIndex = sortSelectRelevanceIndex
        }
    })


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
