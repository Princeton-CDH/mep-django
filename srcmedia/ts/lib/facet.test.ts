import { Subject } from 'rxjs'

import { RxBooleanFacet, RxChoiceFacet } from './facet'

describe('RxBooleanFacet', () => {
    
    beforeEach(() => {
        document.body.innerHTML = `
        <input id="facet" type="checkbox" name="has_card"/>
        <label for="facet">Card<span class="count">0</span></label>
        `
    })
    
    it('stores its count as an observable sequence', () => {
        let $facet = document.querySelector('#facet') as HTMLInputElement
        let rbf = new RxBooleanFacet($facet)
        expect(rbf.count).toBeInstanceOf(Subject)
    })
    
    it('keeps a reference to the count in its label', () => {
        let $facet = document.querySelector('#facet') as HTMLInputElement
        let $count = document.querySelector('.count') as HTMLSpanElement
        let rbf = new RxBooleanFacet($facet)
        expect(rbf.countElement).toBe($count)
    })
    
    it('updates the count element when its count is updated', () => {
        let $facet = document.querySelector('#facet') as HTMLInputElement
        let $count = document.querySelector('.count') as HTMLSpanElement
        let rbf = new RxBooleanFacet($facet)
        rbf.count.subscribe(() => {
            expect($count.innerHTML).toBe('55')
        })
        rbf.count.next(55)
    })
})

describe('RxChoiceFacet', () => {

    beforeEach(() => {
        document.body.innerHTML = `
        <fieldset class="facet">
            <legend>fruits<legend>
            <ul>
                <li>
                    <input id="banana" name="fruits" value="banana" type="checkbox">
                    <label for="banana">banana<span class="count">15</span></label>
                </li>
            </ul>
        </fieldset>`
    })

    it('updates its counts when new ones are supplied', () => {
        const $facet = document.querySelector('.facet') as HTMLFieldSetElement
        const $bananaCountEl = document.querySelector('label[for=banana] .count') as HTMLSpanElement
        const rcf = new RxChoiceFacet($facet)
        rcf.counts.subscribe(() => expect($bananaCountEl.innerHTML).toBe('20'))
        rcf.counts.next(['banana', 20])
    })

    it('displays counts using comma formatting', () => {
        const $facet = document.querySelector('.facet') as HTMLFieldSetElement
        const $bananaCountEl = document.querySelector('label[for=banana] .count') as HTMLSpanElement
        const rcf = new RxChoiceFacet($facet)
        rcf.counts.subscribe(() => expect($bananaCountEl.innerHTML).toBe('2,942'))
        rcf.counts.next(['banana', 2942])
    })

    it('publishes events when the user makes a choice', () => {
        const $facet = document.querySelector('.facet') as HTMLFieldSetElement
        const $banana = document.querySelector('#banana') as HTMLInputElement
        const rcf = new RxChoiceFacet($facet)
        const watcher = jest.fn()
        rcf.events.subscribe(watcher)
        $banana.dispatchEvent(new Event('change', { bubbles: true }))
        expect(watcher).toHaveBeenCalled()
    })
})


