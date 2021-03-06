import PageControls from './PageControls'

beforeEach(() => {
    document.body.innerHTML = `
    <div id="page-controls"/>
        <a rel="prev"/>
        <a rel="next"/>
    </div>`
})

it('finds the next/prev page links and stores a reference to their elements', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const $nextButton = document.querySelector('a[rel=next]') as HTMLAnchorElement
    const $prevButton = document.querySelector('a[rel=prev]') as HTMLAnchorElement
    const pc = new PageControls($el)
    expect(pc.nextButton).toBe($nextButton)
    expect(pc.prevButton).toBe($prevButton)
})

it('converts the next/prev page links into buttons', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const $nextButton = document.querySelector('a[rel=next]') as HTMLAnchorElement
    const $prevButton = document.querySelector('a[rel=prev]') as HTMLAnchorElement
    const pc = new PageControls($el)
    // no longer have href attributes
    expect($nextButton.hasAttribute('href')).toBe(false)
    expect($prevButton.hasAttribute('href')).toBe(false)
    // have the button role
    expect($nextButton.getAttribute('role')).toBe('button')
    expect($prevButton.getAttribute('role')).toBe('button')
})

it('listens to click events on the next/prev page buttons', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const $nextButton = document.querySelector('a[rel=next]') as HTMLAnchorElement
    const $prevButton = document.querySelector('a[rel=prev]') as HTMLAnchorElement
    const pc = new PageControls($el)
    // listen to click events collected in pageChanges
    const watcher = jest.fn()
    pc.pageChanges.subscribe(watcher)
    // create some fake clicks on next/prev buttons and check they're reported
    $nextButton.dispatchEvent(new Event('click'))
    expect(watcher).toHaveBeenCalledWith('next')
    $prevButton.dispatchEvent(new Event('click'))
    expect(watcher).toHaveBeenCalledWith('prev')
})

it('disables next and previous buttons if only one page', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const pc = new PageControls($el)
    return pc.update([1, 1]).then(() => { // on page 1, 1 total pages
        expect(pc.nextButton.hasAttribute('aria-hidden')).toBe(true)
        expect(pc.prevButton.hasAttribute('aria-hidden')).toBe(true)
    })
})

it('disables next button if on the last page', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const pc = new PageControls($el)
    return pc.update([10, 10]).then(() => { // on page 10, 10 total pages
        expect(pc.nextButton.hasAttribute('aria-hidden')).toBe(true)
        expect(pc.prevButton.hasAttribute('aria-hidden')).toBe(false)
    })
})

it('disables prev button if on the first page', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const pc = new PageControls($el)
    return pc.update([1, 10]).then(() => { // on page 1, 10 total pages
        expect(pc.nextButton.hasAttribute('aria-hidden')).toBe(false)
        expect(pc.prevButton.hasAttribute('aria-hidden')).toBe(true)
    })
})

it('allows next/prev to be used if on any other page', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const pc = new PageControls($el)
    return pc.update([5, 10]).then(() => { // on page 5, 10 total pages
        expect(pc.nextButton.hasAttribute('aria-hidden')).toBe(false)
        expect(pc.prevButton.hasAttribute('aria-hidden')).toBe(false)
    })
})
