import MainMenu from './components/MainMenu'
import PageControls from './components/PageControls'

document.addEventListener('DOMContentLoaded', () => {

    // selectors
    const $html = document.firstElementChild as HTMLHtmlElement
    const $openMainMenu = document.getElementById('open-main-menu') as HTMLElement
    const $closeMainMenu = document.getElementById('close-main-menu') as HTMLElement
    const $mainMenu = document.getElementById('main-menu') as HTMLElement
    const $pageControls = document.getElementsByClassName('sort-pages')[0] as HTMLElement

    // components
    const mainMenu = new MainMenu($mainMenu)
    const pageControls = new PageControls($pageControls)

    console.log(pageControls)

    // bindings
    $openMainMenu.onclick = mainMenu.show.bind(mainMenu)
    $closeMainMenu.onclick = mainMenu.hide.bind(mainMenu)

    // setup
    $html.classList.remove('no-js') // remove the 'no-js' class

})
