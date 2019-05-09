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

it('stores value as an observable sequence', () => {
    const element = document.querySelector('select') as HTMLSelectElement
    const rs = new RxSelect(element)
    expect(rs.value).toBeInstanceOf(Subject)
})

it('stores options as an observable sequence', () => {
    const element = document.querySelector('select') as HTMLSelectElement
    const rs = new RxSelect(element)
    expect(rs.options).toBeInstanceOf(Subject)
})

it('stores disabled as an observable sequence', () => {
    const element = document.querySelector('select') as HTMLSelectElement
    const rs = new RxSelect(element)
    expect(rs.disabled).toBeInstanceOf(Subject)
})

it('updates its value when the user chooses an option', done => {
    const element = document.querySelector('select') as HTMLSelectElement
    const option = document.querySelector('option[value=apple]') as HTMLOptionElement
    const rs = new RxSelect(element)
    rs.value.subscribe(value => {
        expect(value).toEqual('apple') // state was updated
        done()
    })
    option.selected = true // manually select a new <option>
    element.dispatchEvent(new Event('input')) // fake an input event
})

it('updates its element when new value is passed in', () => {
    const element = document.querySelector('select') as HTMLSelectElement
    const option = document.querySelector('option[value=orange]') as HTMLOptionElement
    const rs = new RxSelect(element)
    rs.value.next('orange')
    expect(element.value).toBe('orange') // element's value changed
    expect(option.selected).toBe(true) // selected <option> changed
})

it('re-renders itself when new options are passed in', () => {
    const element = document.querySelector('select') as HTMLSelectElement
    const rs = new RxSelect(element)
    const newOptions = [{ value: "banana", text: "banana" }]
    rs.options.next(newOptions)
    expect(element.innerHTML).toBe(`<option value="banana">banana</option>`)
})

it('updates the disabled attribute when disabled is passed in', () => {
    const element = document.querySelector('select') as HTMLSelectElement
    const rs = new RxSelect(element)
    rs.disabled.next(true)
    expect(element.disabled).toBe(true) // element is disabled
})