import Masonry from 'masonry-layout'

// we have to wait for the ENTIRE page to load (not just DOMContentLoaded)
// because image heights won't be calculated otherwise & we will get a fun
// race condition.
window.addEventListener('load', () => {

    /* ELEMENTS */
    const container = document.querySelector('.subpages') as HTMLElement

    /* BINDINGS */
    if (window.matchMedia('(min-width: 1024px)').matches) { // only on desktop
        const masonry = new Masonry(container, {
            itemSelector: '.preview',
            columnWidth: '.grid-sizer', // controlled in css
            gutter: '.gutter-sizer', // controlled in css
            horizontalOrder: true,
        })
    }
})