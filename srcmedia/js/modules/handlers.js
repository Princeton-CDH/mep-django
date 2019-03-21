import { body, mainMenu } from './elements'

/* event handlers */

export const onMainMenuOpen = event => {
    body.then(element => element.style.overflowY = 'hidden') // stop the page from scrolling
}

export const onMainMenuClose = event => {
    body.then(element => element.style.overflowY = null) // allow page to scroll
}