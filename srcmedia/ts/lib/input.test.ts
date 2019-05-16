import { Subject, Observable } from 'rxjs'

import { RxInput, RxTextInput, RxCheckboxInput, RxNumberInput } from './input'

describe('RxInput', () => {

    beforeEach(() => {
        document.body.innerHTML = `<input type="text">`
    })

    it('stores state as an observable sequence', () => {
        class RxFooInput extends RxInput { } // create a fake subclass
        const $element = document.querySelector('input[type=text]') as HTMLInputElement
        const rfi = new RxFooInput($element)
        expect(rfi.state).toBeInstanceOf(Subject)
    })

    it('can update its value', () => {
        class RxFooInput extends RxInput { }
        const $element = document.querySelector('input[type=text]') as HTMLInputElement
        const rfi = new RxFooInput($element)
        return rfi.update({ value: 'sesame' }).then(() => {
            expect($element.value).toBe('sesame')
        })
    })

})

describe('RxTextInput', () => {

    beforeEach(() => {
        document.body.innerHTML = `<input type="text">`
    })

    it('updates when the user types into it', done => {
        const $element = document.querySelector('input[type=text]') as HTMLInputElement
        const rti = new RxTextInput($element)
        rti.state.subscribe(state => { // set up so that test completes once state is updated
            expect(state).toEqual({ value: 'mysearch' })
            expect($element.value).toBe('mysearch')
            done() // done() is needed for async tests so we know when to expect the result
        })
        $element.value = 'mysearch'
        $element.dispatchEvent(new Event('input')) // fake an input event as though the user typed
    })

    it('debounces rapid changes when the user is typing', done => {
        const $element = document.querySelector('input[type=text]') as HTMLInputElement
        const rti = new RxTextInput($element)
        const watcher = jest.fn()
        rti.state.subscribe(watcher)
        rti.state.subscribe(() => {
            expect(watcher).toHaveBeenCalledTimes(1) // only called once
            expect(watcher).toHaveBeenCalledWith({ value: 'mys' }) // only used the final value
            done()
        })
        $element.value = 'm'
        $element.dispatchEvent(new Event('input'))
        $element.value = 'my'
        $element.dispatchEvent(new Event('input'))
        $element.value = 'mys'
        $element.dispatchEvent(new Event('input'))
    })

})

describe('RxCheckboxInput', () => {

    beforeEach(() => {
        document.body.innerHTML = `<input type="checkbox">`
    })

    it('updates when the user toggles it', done => {
        const $element = document.querySelector('input[type=checkbox]') as HTMLInputElement
        const rci = new RxCheckboxInput($element)
        rci.state.subscribe(state => {
            expect(state).toEqual({ checked: true, value: 'on' }) // 'on' is the default value
            expect($element.checked).toBe(true)
            done()
        })
        $element.checked = true
        $element.dispatchEvent(new Event('change')) // fake a change event as though the user toggled it
    })

})

describe('RxNumberInput', () => {

    beforeEach(() => {
        document.body.innerHTML = `<input type="number" min="20" max="50">`
    })

    it('publishes its value as an observable', () => {
        const $element = document.querySelector('input[type=number]') as HTMLInputElement
        const rni  = new RxNumberInput($element)
        expect(rni.value).toBeInstanceOf(Observable)
    })

    it('publishes its validity state as an observable', () => {
        const $element = document.querySelector('input[type=number]') as HTMLInputElement
        const rni  = new RxNumberInput($element)
        expect(rni.valid).toBeInstanceOf(Observable)
    })

    it('updates its value when the user types into it', () => {
        const $element = document.querySelector('input[type=number]') as HTMLInputElement
        const rni  = new RxNumberInput($element)
        rni.value.subscribe(value => expect(value).toBe(35))
        $element.value = '35'
        $element.dispatchEvent(new Event('input'))
    })

    it('debounces rapid changes when the user is typing', done => {
        const $element = document.querySelector('input[type=number]') as HTMLInputElement
        const rni  = new RxNumberInput($element)
        const watcher = jest.fn()
        rni.value.subscribe(watcher)
        rni.value.subscribe(() => {
            expect(watcher).toHaveBeenCalledTimes(1) // only called once
            expect(watcher).toHaveBeenCalledWith(23) // only used the final value
            done()
        })
        $element.value = '2'
        $element.dispatchEvent(new Event('input'))
        $element.value = '26'
        $element.dispatchEvent(new Event('input'))
        $element.value = '23'
        $element.dispatchEvent(new Event('input'))
    })

    it('has a value of NaN if the user didn\'t enter a number', () => {
        const $element = document.querySelector('input[type=number]') as HTMLInputElement
        const rni  = new RxNumberInput($element)
        rni.value.subscribe(value => expect(value).toBeNaN())
        $element.value = 'wrong!'
        $element.dispatchEvent(new Event('input'))
    })

    it('updates its validity state when the value changes', () => {
        const $element = document.querySelector('input[type=number]') as HTMLInputElement
        const rni  = new RxNumberInput($element)
        rni.valid.subscribe(valid => expect(valid).toBe(false))
        $element.value = '100' // too high; above max of 50
        $element.dispatchEvent(new Event('input'))
    })
})