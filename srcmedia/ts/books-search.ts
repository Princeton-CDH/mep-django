import PageControls from './components/PageControls'
import { RxSelect } from './lib/select'

document.addEventListener('DOMContentLoaded', () => {

    // selectors
    const $booksSearchForm = document.getElementById('books-form') as HTMLFormElement
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement
    const $pageSelect = document.querySelector('select[name=page]') as HTMLSelectElement

    // components
    const pageControls = new PageControls($pageControls)
    const pageSelect = new RxSelect($pageSelect)

    // bindings
    pageSelect.value.subscribe(() => $booksSearchForm.submit()) // basic submission
})
