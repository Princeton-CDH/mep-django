import { Subject } from 'rxjs'

import { RxBooleanFacet } from './facet'

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

