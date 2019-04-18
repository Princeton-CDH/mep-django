import { merge } from 'rxjs'
import { pluck } from 'rxjs/operators'

import { RxTextInput, RxCheckboxInput } from './lib/input'
import { RxOutput } from './lib/output'
import { RxSearchForm } from './lib/form'
import { RxSelect } from './lib/select'
import PageControls from './components/PageControls'

document.addEventListener('DOMContentLoaded', () => {

    // selectors
    const $membersSearchForm = document.getElementById('members-form') as HTMLFormElement
    const $keywordInput = document.querySelector('input[name=query]') as HTMLInputElement
    const $hasCardInput = document.querySelector('input[name=has_card]') as HTMLInputElement
    const $resultsOutput = document.querySelector('output[form=members-form]') as HTMLOutputElement
    const $totalResultsOutput = document.querySelector('output.total-results') as HTMLOutputElement
    const $pageSelect = document.querySelector('select[name=page]') as HTMLSelectElement
    const $sortSelect = document.querySelector('select[name=sort]') as HTMLSelectElement
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement

    // components
    const membersSearchForm = new RxSearchForm($membersSearchForm)
    const keywordInput = new RxTextInput($keywordInput)
    const hasCardInput = new RxCheckboxInput($hasCardInput)
    const resultsOutput = new RxOutput($resultsOutput)
    const totalResultsOutput = new RxOutput($totalResultsOutput)
    const pageSelect = new RxSelect($pageSelect)
    const sortSelect = new RxSelect($sortSelect)
    const pageControls = new PageControls($pageControls)

    // bindings
    merge(
        keywordInput.state,
        hasCardInput.state,
        pageSelect.state,
        sortSelect.state,
    ).subscribe(() => {
        membersSearchForm.submit()
        membersSearchForm.element.classList.add('loading') // add 'loading' classes
        resultsOutput.element.classList.add('loading')
    })

    membersSearchForm.state.pipe(pluck('results')).subscribe(results => {
        membersSearchForm.element.classList.remove('loading') // remove 'loading' classes
        resultsOutput.element.classList.remove('loading')
        resultsOutput.update(results) // pass updated results to the output
    }) 
    
})
