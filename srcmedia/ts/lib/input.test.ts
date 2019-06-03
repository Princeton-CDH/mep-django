import { RxInput, RxTextInput, RxCheckboxInput, RxNumberInput } from './input'
import { fakeValueChange, fakeToggle } from './common'

describe('RxInput', () => {

    it('publishes events of EVENT_TYPE on its element as an observable', () => {
        document.body.innerHTML = `<input type="text">`
        jest.useFakeTimers() // non-real-time execution
        class RxFooInput extends RxInput { } // will use EVENT_TYPE 'input' by default
        const $input = document.querySelector('input') as HTMLInputElement
        const rfi = new RxFooInput($input)
        const watcher = jest.fn()
        rfi.events$.subscribe(watcher)
        setTimeout(() => fakeValueChange($input, 'my text'), 100) // change value after 100ms
        jest.runAllTimers()
        expect(watcher).toHaveBeenCalledTimes(1) // called once
        expect(watcher).toHaveBeenCalledWith(expect.any(Event)) // with an Event
    })

    it('publishes validity state starting with the initial state', () => {
        document.body.innerHTML = `
            <input type="text">
            <input type="number" min="10" value="1">
        `
        class RxFooInput extends RxInput { }
        const $textInput = document.querySelector('input[type=text]') as HTMLInputElement
        const $numInput = document.querySelector('input[type=number]') as HTMLInputElement
        const watcher = jest.fn()
        const watcher2 = jest.fn()
        const rfi = new RxFooInput($textInput) // will be valid on creation
        const rfi2 = new RxFooInput($numInput) // will be invalid on creation
        rfi.valid$.subscribe(watcher)
        rfi2.valid$.subscribe(watcher2)
        expect(watcher).toHaveBeenCalledTimes(1)
        expect(watcher).toHaveBeenCalledWith(true) // started out valid
        expect(watcher2).toHaveBeenCalledTimes(1)
        expect(watcher2).toHaveBeenCalledWith(false) // started out invalid
    })

    it('updates validity state when an event occurs', () => {
        document.body.innerHTML = `<input type="number" min="10">`
        class RxFooInput extends RxInput { }
        const $input = document.querySelector('input') as HTMLInputElement
        const rfi = new RxFooInput($input)
        const watcher = jest.fn()
        rfi.valid$.subscribe(watcher)
        expect(watcher).toHaveBeenCalledTimes(1) // receives initial validity
        expect(watcher).toHaveBeenLastCalledWith(true) // currently valid
        fakeValueChange($input, '1') // change to invalid value
        jest.runAllTimers()
        expect(watcher).toHaveBeenCalledTimes(2) // validity was updated
        expect(watcher).toHaveBeenLastCalledWith(false) // input is now invalid
    })
})

describe('RxTextInput', () => {

    beforeEach(() => {
        document.body.innerHTML = `<input type="text">`
    })

    it('publishes its value as an observable, starting with initial value', () => {
        jest.useFakeTimers()
        const $input = document.querySelector('input') as HTMLInputElement
        const rti = new RxTextInput($input)
        const watcher = jest.fn()
        rti.value$.subscribe(watcher)
        expect(watcher).toHaveBeenCalledTimes(1) // called on subscription with current value
        expect(watcher).toHaveBeenLastCalledWith('') // value is empty now
        setTimeout(() => fakeValueChange($input, 'my text'), 100) // later we change the value
        jest.runAllTimers()
        expect(watcher).toHaveBeenCalledTimes(2) // second call
        expect(watcher).toHaveBeenLastCalledWith('my text') // updated with current value
    })
})

describe.skip('RxCheckboxInput', () => {

    beforeEach(() => {
        document.body.innerHTML = `<input type="checkbox" value="test!">`
    })

    it('publishes its state as an observable, starting with initial state', () => {
        jest.useFakeTimers()
        const $input = document.querySelector('input') as HTMLInputElement
        const rti = new RxCheckboxInput($input)
        const watcher = jest.fn()
        rti.checked$.subscribe(watcher)
        expect(watcher).toHaveBeenCalledTimes(1)
        expect(watcher).toHaveBeenLastCalledWith(false) // not currently checked
        setTimeout(() => fakeToggle($input), 100) // check it 100ms later
        jest.runAllTimers()
        expect(watcher).toHaveBeenCalledTimes(2)
        expect(watcher).toHaveBeenLastCalledWith(true) // now checked
    })
})

describe('RxNumberInput', () => {

    beforeEach(() => {
        document.body.innerHTML = `
            <input type="number" min="20" max="50" value="30">
        `
    })

    it('publishes its value as an observable, starting with initial value', () => {
        const $input = document.querySelector('input') as HTMLInputElement
        const rni  = new RxNumberInput($input)
        const watcher = jest.fn()
        rni.value$.subscribe(watcher)
        expect(watcher).toHaveBeenCalledWith(30) // immediately receives current value
    })

    it('parses provided values into integers', () => {
        const $input = document.querySelector('input') as HTMLInputElement
        const rni  = new RxNumberInput($input)
        const watcher = jest.fn()
        rni.value$.subscribe(watcher)
        fakeValueChange($input, '42')
        expect(watcher).toHaveBeenLastCalledWith(42)
    })

    it('publishes NaN for invalid values', () => {
        const $input = document.querySelector('input') as HTMLInputElement
        const rni  = new RxNumberInput($input)
        const watcher = jest.fn()
        rni.value$.subscribe(watcher)
        fakeValueChange($input, 'invalid!')
        expect(watcher).toHaveBeenLastCalledWith(NaN)
    })
})