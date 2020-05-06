import ActiveFilters from './ActiveFilters'

describe('ActiveFilters component', () => {

    beforeEach(() => {
        // make the DOM reflect the currently active filters
        document.body.innerHTML = `
        <div class='active-filters'>
            <span class='legend'>Selected Filters</span>
            <a href='http://example.com/'>United States</a>
            <a href='http://example.com/'>France</a>
            <a href='http://example.com/'>Female</a>
            <a href='http://example.com/'>Has Card</a>
            <a href='http://example.com/'>Member 1920 – 1940</a>
            <a href='http://example.com/' class='clear-all'>Clear All</a>
        </div>
        `
    })

    it('finds the legend element on initialization', () => {
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // keeps reference to legend element
        const $legend = document.querySelector('.legend') as HTMLSpanElement
        expect(af.$legend).toBe($legend)
    })

    it('finds the "clear all" button on initialization', () => {
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // keeps reference to "clear all" button
        const $clearAll = document.querySelector('.clear-all') as HTMLAnchorElement
        expect(af.$clearAll).toBe($clearAll)
    })

    it('converts all links into buttons on initialization', () => {
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // hrefs should be stripped, should get role='button'
        const $anchors = document.querySelectorAll('a')
        $anchors.forEach($anchor => {
            expect($anchor.getAttribute('role')).toBe('button')
            expect($anchor.hasAttribute('href')).toBe(false)
        })
    })

    it('reads boolean filter from querystring on initialization', () => {
        // set up page with boolean filter active
        history.replaceState({}, 'test', 'http://localhost/?is_cool=on')
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // boolean should be stored; value doesn't matter so we use it unchanged
        const watcher = jest.fn()
        af.filters.subscribe(watcher)
        const initState: Map<string, any> = watcher.mock.calls[0][0]
        expect(initState.get('is_cool')).toBe('on')
    })

    it('reads multivalued filter from querystring on initialization', () => {
        // set up page with multivalued text facet active
        history.replaceState({}, 'test', 'http://localhost/?foo=bar&foo=baz')
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // facet values should be collapsed into an array
        const watcher = jest.fn()
        af.filters.subscribe(watcher)
        const initState: Map<string, any> = watcher.mock.calls[0][0]
        expect(initState.get('foo')).toEqual(['bar', 'baz'])
    })

    it('reads range filter from querystring on initialization', () => {
        // set up page with range filter active
        history.replaceState({}, 'test', 'http://localhost/?foo_1=100&foo_2=150')
        const $target = document.querySelector('.active-filters') as HTMLDivElement
        const af = new ActiveFilters($target)

        // both ends of range should be under name of property ('foo')
        const watcher = jest.fn()
        af.filters.subscribe(watcher)
        const initState: Map<string, any> = watcher.mock.calls[0][0]
        expect(initState.get('foo')).toEqual(['100', '150'])
    })

    it.todo('renders a clickable button for each active filter')

    it.todo('removes an active filter button when the user clicks it')

    it.todo('emits an event when the user removes an active filter')

    it.todo('hides the legend and "clear all" button if no active filters')

    it.todo('shows the legend and "clear all" button if filters are active')

})
