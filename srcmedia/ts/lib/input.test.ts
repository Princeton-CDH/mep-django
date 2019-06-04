import { RxInput, RxTextInput, RxCheckboxInput, RxNumberInput } from './input'
import { fakeValueChange, fakeToggle } from './common'

describe('RxInput', () => {

    it('publishes events of EVENT_TYPE on its element as an observable', () => {
        document.body.innerHTML = `<input type="text">`
        class RxFooInput extends RxInput { } // will use EVENT_TYPE 'input' by default
        const $input = document.querySelector('input') as HTMLInputElement
        const rfi = new RxFooInput($input)
        const events = jest.fn()
        rfi.events$.subscribe(events)
        fakeValueChange($input, 'my text') // change value after 100ms
        expect(events).toHaveBeenCalledTimes(1) // called once
        expect(events).toHaveBeenCalledWith(expect.any(Event)) // with an Event
    })

    it('publishes validity state starting with the initial state', () => {
        document.body.innerHTML = `
            <input type="text">
            <input type="number" min="10" value="1">
        `
        class RxFooInput extends RxInput { }
        const $textInput = document.querySelector('input[type=text]') as HTMLInputElement
        const $numInput = document.querySelector('input[type=number]') as HTMLInputElement
        const textValid = jest.fn()
        const numValid = jest.fn()
        const rfiText = new RxFooInput($textInput) // valid on creation
        const rfiNum = new RxFooInput($numInput) // invalid on creation (below min)
        rfiText.valid$.subscribe(textValid)
        rfiNum.valid$.subscribe(numValid)
        expect(textValid).toHaveBeenCalledTimes(1)
        expect(textValid).toHaveBeenCalledWith(true) // started out valid
        expect(numValid).toHaveBeenCalledTimes(1)
        expect(numValid).toHaveBeenCalledWith(false) // started out invalid
    })

    it('updates validity state when an event occurs', () => {
        document.body.innerHTML = `<input type="number" min="10">`
        class RxFooInput extends RxInput { }
        const $input = document.querySelector('input') as HTMLInputElement
        const rfi = new RxFooInput($input)
        const valid = jest.fn()
        rfi.valid$.subscribe(valid)
        expect(valid).toHaveBeenCalledTimes(1) // receives initial validity
        expect(valid).toHaveBeenLastCalledWith(true) // currently valid
        fakeValueChange($input, '1') // change to invalid value
        expect(valid).toHaveBeenCalledTimes(2) // validity was updated
        expect(valid).toHaveBeenLastCalledWith(false) // input is now invalid
    })
})

describe('RxTextInput', () => {

    beforeEach(() => {
        document.body.innerHTML = `<input type="text">`
    })

    it('publishes its value as an observable, starting with initial value', () => {
        const $input = document.querySelector('input') as HTMLInputElement
        const rti = new RxTextInput($input)
        const value = jest.fn()
        rti.value$.subscribe(value)
        expect(value).toHaveBeenCalledTimes(1) // called on subscription with current value
        expect(value).toHaveBeenLastCalledWith('') // value is empty now
        fakeValueChange($input, 'my text') // later we change the value
        expect(value).toHaveBeenCalledTimes(2) // second call
        expect(value).toHaveBeenLastCalledWith('my text') // updated with current value
    })
})

describe.skip('RxCheckboxInput', () => {

    beforeEach(() => {
        document.body.innerHTML = `<input type="checkbox" value="test!">`
    })

    /*
     * FIXME some problem here, potentially with jsdom...the 'change' event
     * isn't being caught; not sure why. tested it in a codepen and seems to
     * behave as expected, so for now keeping this test skipped as it's
     * probably specific to our testing setup.
     */
    it('publishes its state as an observable, starting with initial state', () => {
        const $input = document.querySelector('input') as HTMLInputElement
        const rti = new RxCheckboxInput($input)
        const checked = jest.fn()
        rti.checked$.subscribe(checked)
        expect(checked).toHaveBeenCalledTimes(1)
        expect(checked).toHaveBeenLastCalledWith(false) // not currently checked
        fakeToggle($input) // check it
        expect(checked).toHaveBeenCalledTimes(2)
        expect(checked).toHaveBeenLastCalledWith(true) // now checked
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
        const value = jest.fn()
        rni.value$.subscribe(value)
        expect(value).toHaveBeenCalledWith(30) // immediately receives current value
    })

    it('parses provided values into integers', () => {
        const $input = document.querySelector('input') as HTMLInputElement
        const rni  = new RxNumberInput($input)
        const value = jest.fn()
        rni.value$.subscribe(value)
        fakeValueChange($input, '42')
        expect(value).toHaveBeenLastCalledWith(42)
    })

    it('publishes NaN for non-integer values', () => {
        const $input = document.querySelector('input') as HTMLInputElement
        const rni  = new RxNumberInput($input)
        const value = jest.fn()
        rni.value$.subscribe(value)
        fakeValueChange($input, 'invalid!')
        expect(value).toHaveBeenLastCalledWith(NaN)
    })
})