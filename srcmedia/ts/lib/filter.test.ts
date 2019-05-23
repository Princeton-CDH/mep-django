import { Observable } from 'rxjs'

import { RxRangeFilter } from './filter'

describe('RxRangeFilter', () => {

    beforeEach(() => {
        document.body.innerHTML = `
        <fieldset class="range facet">
            <legend>temperature</legend>
            <input id="start" type="number" min="0">
            <input id="stop" type="number" max="212">
        </fieldset>
        `

        it('stores its values as an observable', () => {
            const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
            const rrf = new RxRangeFilter($facet)
            expect(rrf.values).toBeInstanceOf(Observable)
        })

        it('updates the values when either input changes value', () => {
            const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
            const $start = document.querySelector('#start') as HTMLInputElement
            const $stop = document.querySelector('#end') as HTMLInputElement
            const rrf = new RxRangeFilter($facet)
            rrf.values.subscribe(([start, stop]) => {
                expect(start).toBe(50) // start is 50
                expect(stop).toBeNaN() // stop has no value yet
            })
            $start.value = '50'
            $start.dispatchEvent(new Event('input'))
            rrf.values.subscribe(([start, stop]) => {
                expect(start).toBe(50) // start is still 50
                expect(stop).toBe(100) // stop is now 100
            })
            $stop.value = '100'
            $stop.dispatchEvent(new Event('input'))
        })

        it('only updates if both values are new', done => {
            const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
            const $start = document.querySelector('#start') as HTMLInputElement
            const $stop = document.querySelector('#end') as HTMLInputElement
            const rrf = new RxRangeFilter($facet)
            const watcher = jest.fn()
            rrf.values.subscribe(watcher)
            // set the initial values to 25 and 35
            $start.value = '25'
            $stop.value = '35'
            $start.dispatchEvent(new Event('input'))
            $stop.dispatchEvent(new Event('input'))
            // 250ms later, we change a value
            setTimeout(() => {
                $stop.value = '45'
                $stop.dispatchEvent(new Event('input'))
                // 300ms after that, we change our mind back to orig value
                setTimeout(() => {
                    $stop.value = '35'
                    $stop.dispatchEvent(new Event('input'))
                    // ultimately the values should only be updated once
                    expect(watcher).toHaveBeenCalledTimes(1)
                    // and they should be the original values
                    expect(watcher).toHaveBeenLastCalledWith([25, 35])
                    done()
                }, 300)
            }, 250)
        })

        it('only updates if both values are valid', done => {
            const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
            const $start = document.querySelector('#start') as HTMLInputElement
            const $stop = document.querySelector('#end') as HTMLInputElement
            const rrf = new RxRangeFilter($facet)
            const watcher = jest.fn()
            rrf.values.subscribe(watcher)
            // set the initial values to 25 and 35
            $start.value = '25'
            $stop.value = '35'
            $start.dispatchEvent(new Event('input'))
            $stop.dispatchEvent(new Event('input'))
            // 550ms later, we change a value to something invalid
            setTimeout(() => {
                $stop.value = 'stop!'
                $stop.dispatchEvent(new Event('input'))
                expect(watcher).toHaveBeenCalledTimes(1) // didn't update
                expect(watcher).toHaveBeenLastCalledWith([25, 35])
                done()
            }, 550)
        })

        it('only updates if start is less than or equal to stop', done => {
            const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
            const $start = document.querySelector('#start') as HTMLInputElement
            const $stop = document.querySelector('#end') as HTMLInputElement
            const rrf = new RxRangeFilter($facet)
            const watcher = jest.fn()
            rrf.values.subscribe(watcher)
            // set the initial values to 25 and 35
            $start.value = '25'
            $stop.value = '35'
            $start.dispatchEvent(new Event('input'))
            $stop.dispatchEvent(new Event('input'))
            // 550ms later, we change a value to something invalid
            setTimeout(() => {
                $start.value = '45' // after stop
                $start.dispatchEvent(new Event('input'))
                expect(watcher).toHaveBeenCalledTimes(1) // didn't update
                expect(watcher).toHaveBeenLastCalledWith([25, 35])
                done()
            }, 550)
        })

        it('updates its css class when validity changes', done => {
            const $facet = document.querySelector('.range.facet') as HTMLFieldSetElement
            const $start = document.querySelector('#start') as HTMLInputElement
            const $stop = document.querySelector('#end') as HTMLInputElement
            const rrf = new RxRangeFilter($facet)
            rrf.valid.subscribe(() => expect($facet.classList).toContain('error'))
            // set the initial values to 35 and 25; should add error class
            $start.value = '35'
            $stop.value = '25'
            $start.dispatchEvent(new Event('input'))
            $stop.dispatchEvent(new Event('input'))
            rrf.valid.subscribe(() => {
                expect($facet.classList).not.toContain('error')
                done()
            })
            // set to valid values, should remove class
            $start.value = '25'
            $stop.value = '35'
            $start.dispatchEvent(new Event('input'))
            $stop.dispatchEvent(new Event('input'))
        })
    })
})