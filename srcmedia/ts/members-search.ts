import { merge, fromEvent } from 'rxjs'
import { pluck, map, withLatestFrom, startWith, distinctUntilChanged, mapTo, filter, debounceTime, flatMap, skip, tap } from 'rxjs/operators'

import { arraysAreEqual, toggleTab, pluralize } from './lib/common'
import { RxTextInput } from './lib/input'
import { RxOutput } from './lib/output'
import { RxFacetedSearchForm } from './lib/form'
import { RxSelect } from './lib/select'
import { RxChoiceFacet, RxBooleanFacet, RxTextFacet } from './lib/facet'
import { RxRangeFilter, rangesAreEqual } from './lib/filter'
import ActiveFilters from "./components/ActiveFilters"
import PageControls from './components/PageControls'

document.addEventListener('DOMContentLoaded', () => {

    /* ELEMENTS */
    const $membersSearchForm = document.getElementById('members-form') as HTMLFormElement
    const $keywordInput = document.querySelector('input[name=query]') as HTMLInputElement
    const $hasCardInput = document.querySelector('input[name=has_card]') as HTMLInputElement
    const $resultsOutput = document.querySelector('output.results') as HTMLOutputElement
    const $totalResultsOutput = document.querySelector('output.total-results') as HTMLOutputElement
    const $pageSelect = document.querySelector('select[name=page]') as HTMLSelectElement
    const $sortSelect = document.querySelector('select[name=sort]') as HTMLSelectElement
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement
    const $genderFacet = document.querySelector('#id_gender') as HTMLFieldSetElement
    const $memDateFacet = document.querySelector('#id_membership_dates') as HTMLFieldSetElement
    const $birthDateFacet = document.querySelector('#id_birth_year') as HTMLFieldSetElement
    const $nationalityFacet = document.querySelector('#id_nationality') as HTMLFieldSetElement
    const $arrondissementFacet = document.querySelector('#id_arrondissement') as HTMLFieldSetElement
    const $errors = document.querySelector('div[role=alert].errors')
    const $demographicsTab = document.querySelector('.demographics.tab') as HTMLDivElement
    const $booksTab = document.querySelector('.books.tab') as HTMLDivElement
    const $nationalityExpander = document.querySelector('.expander[aria-controls="id_nationality"]') as HTMLDivElement
    const $arrondissementExpander = document.querySelector('.expander[aria-controls="id_arrondissement"]') as HTMLDivElement
    const $activeFilters = document.querySelector('.active-filters') as HTMLDivElement
    const bottomOfForm = $membersSearchForm.getBoundingClientRect().bottom

    /* COMPONENTS */
    const membersSearchForm = new RxFacetedSearchForm($membersSearchForm)
    const keywordInput = new RxTextInput($keywordInput)
    const hasCardFacet = new RxBooleanFacet($hasCardInput)
    const resultsOutput = new RxOutput($resultsOutput)
    const totalResultsOutput = new RxOutput($totalResultsOutput)
    const pageSelect = new RxSelect($pageSelect)
    const sortSelect = new RxSelect($sortSelect)
    const pageControls = new PageControls($pageControls)
    const genderFacet = new RxChoiceFacet($genderFacet)
    const memDateFacet = new RxRangeFilter($memDateFacet)
    const birthDateFacet = new RxRangeFilter($birthDateFacet)
    const nationalityFacet = new RxTextFacet($nationalityFacet)
    const arrondissementFacet = new RxTextFacet($arrondissementFacet)
    const activeFilters = new ActiveFilters($activeFilters)

    /* OBSERVABLES */
    const currentPage$ = pageSelect.value.pipe(
        startWith(pageSelect.element.value), // start with the current page
        map(p => parseInt(p, 10)), // get a number from a string, for math
        distinctUntilChanged() // only update when changed
    )
    const totalResults$ = membersSearchForm.totalResults.pipe(
        map(t => parseInt(t, 10)),
    )
    const totalPages$ = membersSearchForm.pageLabels.pipe(
        map(l => l.length), // number of page labels tells us the number of pages
        distinctUntilChanged()
    )
    const noResults$ = membersSearchForm.totalResults.pipe(
        map(t => t === '0'), // true if totalResults is '0'
        distinctUntilChanged()
    )
    const keywordChange$ = keywordInput.value$.pipe( // debounced, deduped changes
        skip(1), // ignore initial value
        debounceTime(500),
        distinctUntilChanged()
    )
    const memDateChange$ = memDateFacet.value$.pipe( // debounced, deduped and valid changes
        debounceTime(500), // debounce
        withLatestFrom(memDateFacet.valid$), // check validity
        distinctUntilChanged(([a, aValid], [b, bValid]) => { // for the first entry (used only for comparison),
            return rangesAreEqual(a, b) && (aValid == bValid) // we care whether there was a change in validity OR values
        }),
        skip(1), // for all other entries (used to actually update)
        filter(([range, valid]) => valid), // only accept valid submissions
        map(([range, valid]) => range), // only need range
        distinctUntilChanged(rangesAreEqual) // ignore identical ranges, since we will always have valid ones
    )
    const birthdateChange$ = birthDateFacet.value$.pipe( // debounced, deduped and valid changes
        debounceTime(500), // debounce
        withLatestFrom(birthDateFacet.valid$), // check validity
        distinctUntilChanged(([a, aValid], [b, bValid]) => { // for the first entry (used only for comparison),
            return rangesAreEqual(a, b) && (aValid == bValid) // we care whether there was a change in validity OR values
        }),
        skip(1), // for all other entries (used to actually update)
        filter(([range, valid]) => valid), // only accept valid submissions
        map(([range, valid]) => range), // only need range
        distinctUntilChanged(rangesAreEqual) // ignore identical ranges, since we will always have valid ones
    )

    const noKeyword$ = keywordInput.value$.pipe(
        map(v => v === ''), // true if the value of the keyword input is ''
        distinctUntilChanged()
    )
    const pageLabels$ = membersSearchForm.pageLabels.pipe(
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
    const reloadFacets$ = merge( // a list of all the things that require fetching new facets
        keywordChange$,
        memDateChange$,
        birthdateChange$,
        hasCardFacet.checked$.pipe(skip(1)), // ignore initial
        genderFacet.events,
        nationalityFacet.events,
        arrondissementFacet.events,
    )
    const reloadResults$ = merge( // a list of all the things that require fetching new results (jump to page 1)
        reloadFacets$, // anything that changes facets also triggers new results
        sortSelect.value
    ).pipe(debounceTime(100))
    // slight debounce - otherwise we would get repeated events when e.g.
    // the user types a keyword, which also switches the sort to relevance
    // debounce ensures these are close enough to read as a single event
    const totalResultsText$ = merge(
        totalResults$.pipe(map(t => `${t.toLocaleString()} total result${pluralize(t)}`)), // when there are results, say how many, with a comma
        reloadResults$.pipe(mapTo('Results are loading')) // when loading, replace with this text
    )
    const sort$ = noKeyword$.pipe( // 'name' if no keyword, 'relevance' otherwise
        map(n => n ? 'name' : 'relevance')
    )
    const hasCardCount = membersSearchForm.facets.pipe( // "has card" facet count
        pluck('facet_fields'),
        pluck('has_card'),
        pluck('true'),
        distinctUntilChanged(), // only update when changed
    )
    const genderChoices = membersSearchForm.facets.pipe(
        pluck('facet_fields'),
        pluck('gender'),
        flatMap(Object.entries),
    )
    const nationalityChoices = membersSearchForm.facets.pipe(
        pluck('facet_fields'),
        pluck('nationality'),
        flatMap(Object.entries),
    )
    const arrondissementChoices = membersSearchForm.facets.pipe(
        pluck('facet_fields'),
        pluck('arrondissements'),
        flatMap(Object.entries),
    )

    /* SUBSCRIPTIONS */

    // If there were errors, make sure they're cleared when the form becomes valid
    if ($errors) {
        membersSearchForm.valid.pipe(filter(v => v)).subscribe(() => {
            $errors.remove() // NOTE could use a nicer animation here?
        })
    }

    // If the membership date facet had an error, make sure it's cleared when it becomes valid
    if ($memDateFacet.classList.contains('error')) {
        memDateFacet.valid$.pipe(filter(v => v)).subscribe(() => {
            $memDateFacet.classList.remove('error')
        })
    }

    // If the birth year date facet had an error, make sure it's cleared when it becomes valid
    if ($birthDateFacet.classList.contains('error')) {
        birthDateFacet.valid$.pipe(filter(v => v)).subscribe(() => {
            $birthDateFacet.classList.remove('error')
        })
    }

    // Change the sort depending on if a keyword is active or not
    sort$.subscribe(sortSelect.value)

    // Disable the page selection dropdown if there aren't any results
    noResults$.subscribe(pageSelect.disabled)

    // Update the "has card" facet count
    hasCardCount.subscribe(hasCardFacet.count as any) // not sure why 'any' is necessary...

    // Update the gender facet
    genderChoices.subscribe(genderFacet.counts)

    // Update the nationality facet
    nationalityChoices.subscribe(nationalityFacet.counts)

    // Update the arrondissement facet
    arrondissementChoices.subscribe(arrondissementFacet.counts)

    // When a user changes the form, get new facets
    reloadFacets$.subscribe(() => membersSearchForm.getFacets())

    // When we need new results, go back to page 1
    reloadResults$.subscribe(() => pageSelect.value.next('1'))

    // When the page is changed, submit the form and apply loading styles
    pageSelect.value.subscribe(() => {
        membersSearchForm.getResults()
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

    // Make clicking or pressing space/enter on the tabs toggle them, and also
    // untoggle all other tabs
    merge(
        fromEvent($demographicsTab, 'click'),
        fromEvent($demographicsTab, 'keydown').pipe(
            map(e => (e as KeyboardEvent).code),
            filter(code => code == 'Space' || code == 'Enter')
        )
    )
    .subscribe(() => toggleTab($demographicsTab, [$booksTab]))

    merge(
        fromEvent($booksTab, 'click'),
        fromEvent($booksTab, 'keydown').pipe(
            map(e => (e as KeyboardEvent).code),
            filter(code => code == 'Space' || code == 'Enter')
        )
    )
    .subscribe(() => toggleTab($booksTab, [$demographicsTab]))

    // Make clicking or pressing space/enter on the expanders for facets on
    // mobile toggle their aria-expanded attribute
    merge(
        fromEvent($nationalityExpander, 'click'),
        fromEvent($nationalityExpander, 'keydown').pipe(
            map(e => (e as KeyboardEvent).code),
            filter(code => code == 'Space' || code == 'Enter')
        )
    ).subscribe(() => {
        const expanded = $nationalityExpander.getAttribute('aria-expanded')
        if (expanded === 'false') {
            $nationalityExpander.setAttribute('aria-expanded', 'true')
        }
        else {
            $nationalityExpander.setAttribute('aria-expanded', 'false')
        }
    })

    merge(
        fromEvent($arrondissementExpander, 'click'),
        fromEvent($arrondissementExpander, 'keydown').pipe(
            map(e => (e as KeyboardEvent).code),
            filter(code => code == 'Space' || code == 'Enter')
        )
    ).subscribe(() => {
        const expanded = $arrondissementExpander.getAttribute('aria-expanded')
        if (expanded === 'false') {
            $arrondissementExpander.setAttribute('aria-expanded', 'true')
        }
        else {
            $arrondissementExpander.setAttribute('aria-expanded', 'false')
        }
    })

})
