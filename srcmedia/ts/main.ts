import MainMenu from './components/MainMenu'

document.addEventListener('DOMContentLoaded', () => {

    // selectors
    const $html = document.firstElementChild as HTMLHtmlElement
    const $openMainMenu = document.getElementById('open-main-menu') as HTMLElement
    const $closeMainMenu = document.getElementById('close-main-menu') as HTMLElement
    const $mainMenu = document.getElementById('main-menu') as HTMLElement

    // components
    const mainMenu = new MainMenu($mainMenu)

    // bindings
    $openMainMenu.onclick = mainMenu.show.bind(mainMenu)
    $closeMainMenu.onclick = mainMenu.hide.bind(mainMenu)

    // setup
    $html.classList.remove('no-js') // remove the 'no-js' class

})
