function sticky(element: HTMLElement): void {
    // Variables
    let stuck: boolean = false
    let ticking: boolean = false
    let top: number = 0
    // Check top
    let t = window
        .getComputedStyle(element)
        .getPropertyValue('top')
    // Convert a css value like '50px' to integer pixels
    if (t) top = parseFloat(t)
    // Create the scroll event listener
    const scroll = () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                if (element.getBoundingClientRect().top == top && !stuck) {
                    stuck = true
                    element.classList.add('stuck')
                }
                else if (element.getBoundingClientRect().top != top && stuck) {
                    stuck = false
                    element.classList.remove('stuck')
                }
                ticking = false
            })
            ticking = true
        }
    }
    // Bind the scroll event listener
    window.addEventListener('scroll', scroll)
}

export {
    sticky
}