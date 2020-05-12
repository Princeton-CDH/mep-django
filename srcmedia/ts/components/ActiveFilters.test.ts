import ActiveFilters from './ActiveFilters'

describe('ActiveFilters component', () => {

    it('finds needed DOM elements on initialization', () => {
        // set up the DOM with no active filters
        document.body.innerHTML = `
        <form id="test-form"><div class="active-filters hidden"><div class="inner">
            <span class="legend">Selected Filters</span>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div></div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const $form = document.querySelector('form') as HTMLFormElement
        const $clearAll = document.querySelector('.clear-all') as HTMLAnchorElement
        const $inner = document.querySelector('.inner') as HTMLDivElement
        
        const af = new ActiveFilters($target)

        expect(af.$form).toBe($form)            // parent form
        expect(af.$clearAll).toBe($clearAll)    // 'clear all' button
        expect(af.$inner).toBe($inner)          // container for filter buttons
    })

    it('converts all links into buttons on initialization', () => {
        // set up the DOM with some active filters
        document.body.innerHTML = `
        <form id="test-form"><div class="active-filters"><div class="inner">
            <span class="legend">Selected Filters</span>
            <a href="http://example.com/">United States</a>
            <a href="http://example.com/">France</a>
            <a href="http://example.com/">Female</a>
            <a href="http://example.com/">Has Card</a>
            <a href="http://example.com/">Member 1920 – 1940</a>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div></div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // all a hrefs should be stripped, should get role='button'
        const $anchors = document.querySelectorAll('a')
        $anchors.forEach($anchor => {
            expect($anchor.getAttribute('role')).toBe('button')
            expect($anchor.hasAttribute('href')).toBe(false)
        })
    })

    it('adds filter buttons when inputs are activated', () => {
        // set up the DOM with no active filters and some test inputs
        document.body.innerHTML = `
        <form id="test-form">
        <input id="sprinkles" type="checkbox" name="add_sprinkles">
        <label for="flavors_0">Chocolate</label>
        <input id="flavors_0" type="checkbox" name="flavors" value="chocolate">
        <label for="flavors_1">Vanilla</label>
        <input id="flavors_1" type="checkbox" name="flavors" value="vanilla">
        <fieldset>
            <legend>Scoops</legend>
            <input id="scoops_0" type="number" name="scoops_0">
            <input id="scoops_1" type="number" name="scoops_1">
        </fieldset>
        <div class="active-filters hidden"><div class="inner">
            <span class="legend">Selected Filters</span>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div></div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // activate a boolean filter and check its button
        const $boolFilter = document.getElementById('sprinkles') as HTMLInputElement
        $boolFilter.checked = true
        $boolFilter.dispatchEvent(new Event('input', { bubbles: true }))
        const $boolButton = document.querySelector('a[data-input=sprinkles]') as HTMLAnchorElement
        expect($boolButton).not.toBeNull()
        expect($boolButton.dataset.input).toEqual('sprinkles')
        expect($boolButton.getAttribute('role')).toEqual('button')
        expect($boolButton.textContent).toBe('Add Sprinkles')
    })

    it.todo('removes filter buttons when their inputs are cleared')

    it.todo('clears inputs when their filter buttons are clicked')

    it.todo('hides the display if no filters are active')

    it.todo('shows the display if filters are active')

})
