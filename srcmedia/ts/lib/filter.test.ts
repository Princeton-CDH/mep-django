import { RxRangeFilter, rangesAreEqual } from './filter'
import { fakeValueChange } from './common'

describe('RxRangeFilter', () => {

    beforeEach(() => {
        document.body.innerHTML = `
        <fieldset class="range facet">
            <legend>temperature</legend>
            <input id="start" type="number" min="0">
            <input id="stop" type="number" max="212">
        </fieldset>
        `
    })

    it('publishes its values as an observable, starting with initial values', () => {
        const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
        const rrf = new RxRangeFilter($facet)
        const values = jest.fn()
        rrf.value$.subscribe(values)
        expect(values).toHaveBeenCalledWith([NaN, NaN]) // both empty
    })

    it('publishes its validity as an observable, starting with initial validity', () => {
        const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
        const rrf = new RxRangeFilter($facet)
        const valid = jest.fn()
        rrf.valid$.subscribe(valid)
        expect(valid).toHaveBeenCalledWith(true) // both are allowed to be empty, since not required
    })

    it('updates the values when either input changes value', () => {
        jest.useFakeTimers()
        const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
        const $start = document.querySelector('#start') as HTMLInputElement
        const $stop = document.querySelector('#stop') as HTMLInputElement
        const rrf = new RxRangeFilter($facet)
        const values = jest.fn()
        rrf.value$.subscribe(values)
        setTimeout(() => fakeValueChange($start, '50'), 100) // after 100ms start = 50
        setTimeout(() => fakeValueChange($stop, '100'), 200) // after 250ms stop = 100
        jest.runAllTimers()
        expect(values).toHaveBeenNthCalledWith(1, [NaN, NaN]) // initial values
        expect(values).toHaveBeenNthCalledWith(2, [50, NaN]) // after first change
        expect(values).toHaveBeenNthCalledWith(3, [50, 100]) // after second change
    })

    it('becomes invalid if either input is invalid', () => {
        const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
        const $start = document.querySelector('#start') as HTMLInputElement
        const $stop = document.querySelector('#stop') as HTMLInputElement
        const rrf = new RxRangeFilter($facet)
        const valid = jest.fn()
        rrf.valid$.subscribe(valid)
        expect(valid).toHaveBeenLastCalledWith(true) // valid since inputs are empty
        fakeValueChange($start, '-20') // start becomes invalid (below min)
        expect(valid).toHaveBeenLastCalledWith(false) // has become false
        fakeValueChange($start, '35') // start becomes valid
        fakeValueChange($stop, '550') // stop becomes invalid (above max)
        expect(valid).toHaveBeenLastCalledWith(false) // still false
    })

    it('becomes invalid if values are not sequential', () => {
        const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
        const $start = document.querySelector('#start') as HTMLInputElement
        const $stop = document.querySelector('#stop') as HTMLInputElement
        const rrf = new RxRangeFilter($facet)
        const valid = jest.fn()
        rrf.valid$.subscribe(valid)
        expect(valid).toHaveBeenLastCalledWith(true) // valid; both empty/NaN
        fakeValueChange($start, '100')
        fakeValueChange($stop, '50') // less than start
        expect(valid).toHaveBeenLastCalledWith(false) // invalid; start > stop
    })

    it('is valid if both inputs are sequential or equal', () => {
        const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
        const $start = document.querySelector('#start') as HTMLInputElement
        const $stop = document.querySelector('#stop') as HTMLInputElement
        const rrf = new RxRangeFilter($facet)
        const valid = jest.fn()
        rrf.valid$.subscribe(valid)
        fakeValueChange($start, '50')
        fakeValueChange($stop, '100')
        expect(valid).toHaveBeenLastCalledWith(true) // valid; start < stop
        fakeValueChange($start, '111')
        fakeValueChange($stop, '111')
        expect(valid).toHaveBeenLastCalledWith(true) // valid; start = stop
    })
})

describe('rangesAreEqual', () => {

    it('treats ranges with same start and same stop as equal', () => {
        expect(rangesAreEqual([1, 10], [1, 10])).toBe(true)
    })

    it('treats ranges where both starts are NaN as equal', () => {
        expect(rangesAreEqual([NaN, 10], [NaN, 10])).toBe(true)
    })

    it('treats ranges where both stops are NaN as equal', () => {
        expect(rangesAreEqual([1, NaN], [1, NaN])).toBe(true)
    })

    it('treats ranges where all values are NaN as equal', () => {
        expect(rangesAreEqual([NaN, NaN], [NaN, NaN])).toBe(true)
    })

    it('treats ranges with different start as unequal', () => {
        expect(rangesAreEqual([1, 10], [2, 10])).toBe(false)
    })

    it('treats ranges with different stop as unequal', () => {
        expect(rangesAreEqual([1, 10], [1, 11])).toBe(false)
    })

    it('treats ranges where NaN is start or stop as unequal', () => {
        expect(rangesAreEqual([NaN, 10], [1, 10])).toBe(false)
        expect(rangesAreEqual([1, 10], [1, NaN])).toBe(false)
    })
})