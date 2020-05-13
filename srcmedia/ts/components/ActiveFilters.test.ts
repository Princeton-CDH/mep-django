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
        <fieldset id="scoops">
            <legend>Scoops</legend>
            <input id="scoops_0" type="number" name="scoops_0">
            <input id="scoops_1" type="number" name="scoops_1">
        </fieldset>
        <div class="active-filters"><div class="inner">
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
        expect($boolButton.getAttribute('role')).toEqual('button')
        expect($boolButton.textContent).toBe('Add Sprinkles')

        // activate a text facet and check its buttons
        const $textFacet1 = document.getElementById('flavors_0') as HTMLInputElement
        const $textFacet2 = document.getElementById('flavors_1') as HTMLInputElement
        $textFacet1.checked = true
        $textFacet2.checked = true
        $textFacet1.dispatchEvent(new Event('input', { bubbles: true }))
        $textFacet2.dispatchEvent(new Event('input', { bubbles: true }))
        const $textFacet1Button = document.querySelector('a[data-input=flavors_0]') as HTMLAnchorElement
        const $textFacet2Button = document.querySelector('a[data-input=flavors_1]') as HTMLAnchorElement
        [$textFacet1Button, $textFacet2Button].forEach($button => {
            expect($button).not.toBeNull()
            expect($button.getAttribute('role')).toEqual('button')
        })
        expect($textFacet1Button.textContent).toBe('Chocolate')
        expect($textFacet2Button.textContent).toBe('Vanilla')

        // activate a range filter and check its button
        const $rangeFilterMin = document.getElementById('scoops_0') as HTMLInputElement
        const $rangeFilterMax = document.getElementById('scoops_1') as HTMLInputElement
        $rangeFilterMin.value = '2'
        $rangeFilterMin.dispatchEvent(new Event('input', { bubbles: true }))
        let $rangeFilterButton = document.querySelector('a[data-fieldset=scoops]') as HTMLAnchorElement
        expect($rangeFilterButton).not.toBeNull()
        expect($rangeFilterButton.getAttribute('role')).toEqual('button')
        expect($rangeFilterButton.textContent).toEqual('Scoops: 2 – ')
        $rangeFilterMax.value = '4'
        $rangeFilterMax.dispatchEvent(new Event('input', { bubbles: true }))
        expect($rangeFilterButton.innerText).toEqual('Scoops: 2 – 4')
    })

    it('removes filter buttons when their inputs are cleared', () => {
        // set up the DOM with active filters and some test inputs
        document.body.innerHTML = `
        <form id="test-form">
        <input id="sprinkles" type="checkbox" name="add_sprinkles" checked="">
        <label for="flavors_0">Chocolate</label>
        <input id="flavors_0" type="checkbox" name="flavors" value="chocolate" checked="">
        <label for="flavors_1">Vanilla</label>
        <input id="flavors_1" type="checkbox" name="flavors" value="vanilla" checked="">
        <fieldset id="scoops">
            <legend>Scoops</legend>
            <input id="scoops_0" type="number" name="scoops_0" value="1">
            <input id="scoops_1" type="number" name="scoops_1" value="3">
        </fieldset>
        <div class="active-filters"><div class="inner">
            <span class="legend">Selected Filters</span>
            <a role="button" data-input="sprinkles">Add Sprinkles</a>
            <a role="button" data-input="flavors_0">Chocolate</a>
            <a role="button" data-input="flavors_1">Vanilla</a>
            <a role="button" ata-fieldset="scoops">Scoops: 1 – 3</a>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div></div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // boolean filter button goes away when it's deselected
        const $boolFilter = document.getElementById('sprinkles') as HTMLInputElement
        $boolFilter.checked = false
        $boolFilter.dispatchEvent(new Event('input', { bubbles: true }))
        const $boolButton = document.querySelector('a[data-input=sprinkles]') as HTMLAnchorElement
        expect($boolButton).toBeNull()
        
        // text facet buttons go away when they're deselected
        const $textFacet1 = document.getElementById('flavors_0') as HTMLInputElement
        const $textFacet2 = document.getElementById('flavors_1') as HTMLInputElement
        $textFacet1.checked = false
        $textFacet2.checked = false
        $textFacet1.dispatchEvent(new Event('input', { bubbles: true }))
        $textFacet2.dispatchEvent(new Event('input', { bubbles: true }))
        const $textFacet1Button = document.querySelector('a[data-input=flavors_0]') as HTMLAnchorElement
        const $textFacet2Button = document.querySelector('a[data-input=flavors_1]') as HTMLAnchorElement
        expect($textFacet1Button).toBeNull()
        expect($textFacet2Button).toBeNull()

        // range filter button goes away when both inputs empty (not before!)
        const $rangeFilterMin = document.getElementById('scoops_0') as HTMLInputElement
        const $rangeFilterMax = document.getElementById('scoops_1') as HTMLInputElement
        $rangeFilterMin.value = ''
        $rangeFilterMin.dispatchEvent(new Event('input', { bubbles: true }))
        let $rangeFilterButton = document.querySelector('a[data-fieldset=scoops]') as HTMLAnchorElement
        expect($rangeFilterButton).not.toBeNull()
        $rangeFilterMax.value = ''
        $rangeFilterMax.dispatchEvent(new Event('input', { bubbles: true }))
        $rangeFilterButton = document.querySelector('a[data-fieldset=scoops]') as HTMLAnchorElement
        expect($rangeFilterButton).toBeNull()
    })

    it('clears inputs when their filter buttons are clicked', () => {
        // set up the DOM with active filters and some test inputs
        document.body.innerHTML = `
        <form id="test-form">
        <input id="sprinkles" type="checkbox" name="add_sprinkles" checked="">
        <label for="flavors_0">Chocolate</label>
        <input id="flavors_0" type="checkbox" name="flavors" value="chocolate" checked="">
        <label for="flavors_1">Vanilla</label>
        <input id="flavors_1" type="checkbox" name="flavors" value="vanilla" checked="">
        <fieldset id="scoops">
            <legend>Scoops</legend>
            <input id="scoops_0" type="number" name="scoops_0" value="1">
            <input id="scoops_1" type="number" name="scoops_1" value="3">
        </fieldset>
        <div class="active-filters"><div class="inner">
            <span class="legend">Selected Filters</span>
            <a role="button" data-input="sprinkles">Add Sprinkles</a>
            <a role="button" data-input="flavors_0">Chocolate</a>
            <a role="button" data-input="flavors_1">Vanilla</a>
            <a role="button" data-fieldset="scoops">Scoops: 1 – 3</a>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div></div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)
        
        // boolean filter is unchecked when its button is clicked
        const $boolButton = document.querySelector('a[data-input=sprinkles]') as HTMLAnchorElement
        $boolButton.dispatchEvent(new Event('click'))
        const $boolFilter = document.getElementById('sprinkles') as HTMLInputElement
        expect($boolFilter.checked).toBe(false)

        // text facets are unchecked when their buttons are clicked
        const $textFacet1Button = document.querySelector('a[data-input=flavors_0]') as HTMLAnchorElement
        $textFacet1Button.dispatchEvent(new Event('click'))
        const $textFacet1 = document.getElementById('flavors_0') as HTMLInputElement
        expect($textFacet1.checked).toBe(false)
        const $textFacet2Button = document.querySelector('a[data-input=flavors_1]') as HTMLAnchorElement
        $textFacet2Button.dispatchEvent(new Event('click'))
        const $textFacet2 = document.getElementById('flavors_1') as HTMLInputElement
        expect($textFacet2.checked).toBe(false)

        // range filter inputs are both cleared when their button is clicked
        const $rangeFilterButton = document.querySelector('a[data-fieldset=scoops]') as HTMLAnchorElement
        $rangeFilterButton.dispatchEvent(new Event('click'))
        const $rangeFilterMin = document.getElementById('scoops_0') as HTMLInputElement
        const $rangeFilterMax = document.getElementById('scoops_1') as HTMLInputElement
        expect($rangeFilterMin.value).toEqual('')
        expect($rangeFilterMax.value).toEqual('')
    })

    it('hides the display if no filters are active', () => {
        // set up the DOM with an active filter
        document.body.innerHTML = `
        <form id="test-form">
        <input id="sprinkles" type="checkbox" name="add_sprinkles" checked="">
        <div class="active-filters"><div class="inner">
            <span class="legend">Selected Filters</span>
            <a role="button" data-input="sprinkles">Add Sprinkles</a>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div></div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // remove the filter; .active-filters should be .hidden
        const $boolButton = document.querySelector('a[data-input=sprinkles]') as HTMLAnchorElement
        $boolButton.dispatchEvent(new Event('click'))
        expect(af.element.classList).toContain('hidden')
    })

    it('shows the display if filters are active', () => {
        // set up the DOM with an active filter
        document.body.innerHTML = `
        <form id="test-form">
        <input id="sprinkles" type="checkbox" name="add_sprinkles">
        <div class="active-filters hidden"><div class="inner">
            <span class="legend">Selected Filters</span>
            <a href="http://example.com/" class="clear-all">Clear All</a>
        </div></div></form>`
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // active boolean filter; .active-filters should no longer be .hidden
        const $boolFilter = document.getElementById('sprinkles') as HTMLInputElement
        $boolFilter.checked = true
        $boolFilter.dispatchEvent(new Event('input', { bubbles: true }))
        expect(af.element.classList).not.toContain('hidden')
    })
})
