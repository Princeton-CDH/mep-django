import { openMainMenuButton, closeMainMenuButton } from './modules/elements'
import { onMainMenuOpen, onMainMenuClose } from './modules/handlers'

/* page setup */

openMainMenuButton.then(element => element.onclick = onMainMenuOpen)
closeMainMenuButton.then(element => element.onclick = onMainMenuClose)