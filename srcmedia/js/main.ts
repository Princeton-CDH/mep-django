import MainMenu from './components/MainMenu'

document.addEventListener('DOMContentLoaded', () => {

    // selectors
    const $html = document.getElementsByTagName('html')[0] as HTMLHtmlElement
    const $body = document.getElementsByTagName('body')[0] as HTMLBodyElement
    const $openMainMenu = document.getElementById('open-main-menu') as HTMLElement
    const $closeMainMenu = document.getElementById('close-main-menu') as HTMLElement
    const $mainMenu = document.getElementById('main-menu') as HTMLElement

    // components
    const mainMenu = new MainMenu($mainMenu, $body)

    // bindings
    $openMainMenu.onclick = mainMenu.show.bind(mainMenu)
    $closeMainMenu.onclick = mainMenu.hide.bind(mainMenu)

    // setup
    $html.classList.remove('no-js') // remove the 'no-js' class

})
