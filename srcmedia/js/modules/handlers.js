import { body, mainMenu } from './elements'

/* event handlers */

export const onMainMenuOpen = event => {
    event.preventDefault() // don't append #main-menu to address bar or history
    mainMenu.then(element => { // show menu and make it interactive
        element.style.opacity = 1
        element.style.pointerEvents = 'all'
    })
    body.then(element => element.style.overflowY = 'hidden') // stop the page from scrolling
}

export const onMainMenuClose = event => {
    event.preventDefault() // don't append # to address bar or history
    mainMenu.then(element => { // hide menu and make it noninteractive
        element.style.opacity = 0
        element.style.pointerEvents = 'none'
    })
    body.then(element => element.style.overflowY = null) // allow page to scroll
}