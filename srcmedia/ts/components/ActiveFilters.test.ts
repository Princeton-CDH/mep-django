import ActiveFilters from './ActiveFilters'

describe('ActiveFilters component', () => {

    it('finds the parent form on initialization', () => {
        // set up the DOM with no active filters
        document.body.innerHTML = `
        <form id="test-form">
        <div class="active-filters">
            <span class="legend hidden">Selected Filters</span>
            <a href="http://example.com/" class="clear-all hidden">Clear All</a>
        </div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // keeps reference to parent form
        const $form = document.querySelector('form') as HTMLFormElement
        expect(af.$form).toBe($form)
    })

    it('finds the legend element on initialization', () => {
        // set up the DOM with no active filters
        document.body.innerHTML = `
        <form id="test-form">
        <div class="active-filters">
            <span class="legend hidden">Selected Filters</span>
            <a href="http://example.com/" class="clear-all hidden">Clear All</a>
        </div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // keeps reference to legend element
        const $legend = document.querySelector('.legend') as HTMLSpanElement
        expect(af.$legend).toBe($legend)
    })

    it('finds the "clear all" button on initialization', () => {
        // set up the DOM with no active filters
        document.body.innerHTML = `
        <form id="test-form">
        <div class="active-filters">
            <span class="legend hidden">Selected Filters</span>
            <a href="http://example.com/" class="clear-all hidden">Clear All</a>
        </div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // keeps reference to "clear all" button
        const $clearAll = document.querySelector('.clear-all') as HTMLAnchorElement
        expect(af.$clearAll).toBe($clearAll)
    })

    it('converts all links into buttons on initialization', () => {
        // set up the DOM with some active filters
        document.body.innerHTML = `
        <form id="test-form">
        <div class='active-filters'>
            <span class='legend'>Selected Filters</span>
            <a href='http://example.com/'>United States</a>
            <a href='http://example.com/'>France</a>
            <a href='http://example.com/'>Female</a>
            <a href='http://example.com/'>Has Card</a>
            <a href='http://example.com/'>Member 1920 – 1940</a>
            <a href='http://example.com/' class='clear-all'>Clear All</a>
        </div></form>
        `
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // all a hrefs should be stripped, should get role='button'
        const $anchors = document.querySelectorAll('a')
        $anchors.forEach($anchor => {
            expect($anchor.getAttribute('role')).toBe('button')
            expect($anchor.hasAttribute('href')).toBe(false)
        })
    })

    it.skip('reads boolean filter from form on initialization', () => {
        // set up page with a boolean filter active
        document.body.innerHTML = `
        <form id="test-form">
        <input type="checkbox" name="foo" checked="">
        <div class="active-filters">
            <span class="legend">Selected Filters</span>
            <a href="http://example.com/">Is Cool</a>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div>
        </form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // boolean should be stored; value doesn't matter so we use it unchanged
    })

    it.skip('reads multivalued filter from form on initialization', () => {
        // set up page with multivalued text facet active
        document.body.innerHTML = `
        <form id="test-form">
        <div class="active-filters">
            <span class="legend">Selected Filters</span>
            <a href="http://example.com/">Bar</a>
            <a href="http://example.com/">Baz</a>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // facet values should be collapsed into an array
    })

    it.skip('reads range filter from form on initialization', () => {
        // set up page with range filter active
        document.body.innerHTML = `
        <form id="test-form">
        <div class="active-filters">
            <span class="legend">Selected Filters</span>
            <a href="http://example.com/">Foo: 100 - 150</a>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // both ends of range should be under name of property ('foo')
    })

    it.todo('renders a clickable button for each active filter', () => {
        // set up the DOM with no active filters
        document.body.innerHTML = `
        <div class="active-filters">
            <span class="legend hidden">Selected Filters</span>
            <a href="http://example.com/" class="clear-all hidden">Clear All</a>
        </div>`

    })

    it.todo('removes an active filter button when the user clicks it')

    it.todo('emits an event when the user removes an active filter')

    it.todo('hides the legend and "clear all" button if no active filters')

    it.todo('shows the legend and "clear all" button if filters are active')

})
