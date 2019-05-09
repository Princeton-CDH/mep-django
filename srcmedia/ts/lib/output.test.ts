import { Subject } from 'rxjs'

import { RxOutput } from './output'

beforeEach(() => {
    document.body.innerHTML = `<output></output>`
})

it('stores state as an observable sequence', () => {
    const element = document.querySelector('output') as HTMLOutputElement
    const ro = new RxOutput(element)
    expect(ro.state).toBeInstanceOf(Subject)
})

it('injects content directly into itself on update', done => {
    const results = `<div class="results"></div>`
    const element = document.querySelector('output') as HTMLOutputElement
    const ro = new RxOutput(element)
    ro.state.subscribe(() => { // when state changes, we check it's correct
        expect(element.innerHTML).toBe(results)
        done()
    })
    ro.update(results)
})