import { Component, arraysAreEqual } from './common'

describe('Component', () => {

    it('keeps a reference to its element', () => {
        document.body.innerHTML = `<div></div>`
        const element = document.querySelector('div') as HTMLDivElement
        const c = new Component(element)
        expect(c.element).toBe(element)
    })

})

describe('arraysAreEqual', () => {

    it('succeeds if arrays are identical', () => {
        const a = ['a', 1, true]
        const b = ['a', 1, true]
        expect(arraysAreEqual(a, b)).toBe(true)
    })
    
    it('succeeds if arrays are empty', () => {
        const a = [] as any
        const b = [] as any
        expect(arraysAreEqual(a, b)).toBe(true)
    })

    it('fails if arrays contain different elements', () => {
        const a = ['a', 'b']
        const b = ['a', 'c']
        expect(arraysAreEqual(a, b)).toBe(false)
    })

    it('fails if arrays are different lengths', () => {
        const a = ['a']
        const b = ['a', 'a']
        expect(arraysAreEqual(a, b)).toBe(false)
    })

    it('fails if array elements are different types', () => {
        const a = ['a', 1]
        const b = ['a', '1']
        expect(arraysAreEqual(a, b)).toBe(false)
    })

})