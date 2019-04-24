import { Subject } from 'rxjs'

import { RxSelect } from './select'

beforeEach(() => {
    document.body.innerHTML = `
    <select name="fruits">
        <option value="apple">apple</option>
        <option value="orange">orange</option>
    </select>
    `
})

it('stores state as an observable sequence', () => {
    const element = document.querySelector('select') as HTMLSelectElement
    const rs = new RxSelect(element)
    expect(rs.state).toBeInstanceOf(Subject)
})

it('updates its state and element when the user chooses an option', () => {
    const element = document.querySelector('select') as HTMLSelectElement
    const option = document.querySelector('option[value=apple]') as HTMLOptionElement
    const rs = new RxSelect(element)
    rs.state.subscribe(state => {
        expect(state).toEqual({ value: 'apple' }) // state was updated
        expect(element.value).toBe('apple') // element's value was changed
    })
    option.selected = true // manually select a new <option>
    element.dispatchEvent(new Event('input')) // fake an input event
})

it('updates its state and element when update() is called', () => {
    const element = document.querySelector('select') as HTMLSelectElement
    const option = document.querySelector('option[value=orange]') as HTMLOptionElement
    const rs = new RxSelect(element)
    rs.state.subscribe(state => {
        expect(state).toEqual({ value: 'orange' }) // state was updated
        expect(element.value).toBe('orange') // element's value changed
        expect(option.selected).toBe(true) // selected <option> changed
    })
    rs.update({ value: 'orange' })
})