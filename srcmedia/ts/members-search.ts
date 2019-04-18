import { pluck } from 'rxjs/operators'

import { RxTextInput } from './lib/input'
import { RxOutput } from './lib/output'
import { RxSearchForm } from './lib/form'
import PageControls from './components/PageControls'

document.addEventListener('DOMContentLoaded', () => {

    // selectors
    const $membersSearchForm = document.getElementById('members-form') as HTMLFormElement
    const $keywordInput = document.querySelector('input[name=query]') as HTMLInputElement
    const $resultsOutput = document.querySelector('output[form=members-form]') as HTMLOutputElement
    const $totalResultsOutput = document.querySelector('output.total-results') as HTMLOutputElement
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement

    // components
    const membersSearchForm = new RxSearchForm($membersSearchForm)
    const keywordInput = new RxTextInput($keywordInput)
    const resultsOutput = new RxOutput($resultsOutput)
    const totalResultsOutput = new RxOutput($totalResultsOutput)
    const pageControls = new PageControls($pageControls)

    // bindings
    keywordInput.state.subscribe(membersSearchForm.submit) // submit form when keyword changes
    membersSearchForm.state.pipe(pluck('results')).subscribe(resultsOutput.update.bind(resultsOutput)) // pass updated results to the output
    
})
