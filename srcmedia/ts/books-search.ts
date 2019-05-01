import PageControls from './components/PageControls'

document.addEventListener('DOMContentLoaded', () => {

    // selectors
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement

    // components
    const pageControls = new PageControls($pageControls)
    
})
