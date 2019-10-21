import { Component, arraysAreEqual, getTransitionDuration, toggleTab, pluralize } from './common'

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

describe('getTransitionDuration', () => {

    beforeEach(() => {
        document.body.innerHTML = `<div id="main-menu"></div>`
    })

    test('uses a transition duration of zero if none is provided', () => {
        let element = document.getElementById('main-menu') as HTMLElement
        expect(getTransitionDuration(element)).toBe(0)
    })

    test('parses and stores a css transition-duration in ms units', () => {
        let element = document.getElementById('main-menu') as HTMLElement
        element.style.transitionDuration = '500ms'
        expect(getTransitionDuration(element)).toBe(500)
    })

    test('parses and stores a css transition-duration in s units', () => {
        let element = document.getElementById('main-menu') as HTMLElement
        element.style.transitionDuration = '1s'
        expect(getTransitionDuration(element)).toBe(1000)
    })

})

describe('toggleTab', () => {

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="tab1" aria-selected="false"/>
            <div id="tab2" aria-selected="false"/>
            <div id="tab3"" aria-selected="false"/>`
    })

    test('does nothing if the tab is disabled', () => {
        let $tab1 = document.getElementById('tab1') as HTMLDivElement
        let $tab2 = document.getElementById('tab2') as HTMLDivElement
        let $tab3 = document.getElementById('tab3') as HTMLDivElement
        $tab1.toggleAttribute('aria-disabled')
        toggleTab($tab1, [])
        expect($tab1.getAttribute('aria-selected')).toBe('false')
        expect($tab2.getAttribute('aria-selected')).toBe('false')
        expect($tab3.getAttribute('aria-selected')).toBe('false')
    })

    test('sets aria-selected to true if it is false', () => {
        let $tab1 = document.getElementById('tab1') as HTMLDivElement
        toggleTab($tab1, [])
        expect($tab1.getAttribute('aria-selected')).toBe('true')
    })

    test('sets aria-selected to false if it is true', () => {
        let $tab1 = document.getElementById('tab1') as HTMLDivElement
        $tab1.setAttribute('aria-selected', 'true')
        toggleTab($tab1, [])
        expect($tab1.getAttribute('aria-selected')).toBe('false')
    })

    test('sets aria-selected to true if it is not set', () => {
        let $tab1 = document.getElementById('tab1') as HTMLDivElement
        $tab1.removeAttribute('aria-selected')
        toggleTab($tab1, [])
        expect($tab1.getAttribute('aria-selected')).toBe('true')
    })

    test('sets $others aria-selected to false if $element is selected', () => {
        let $tab1 = document.getElementById('tab1') as HTMLDivElement
        let $tab2 = document.getElementById('tab2') as HTMLDivElement
        let $tab3 = document.getElementById('tab3') as HTMLDivElement
        toggleTab($tab1, [$tab2, $tab3])
        expect($tab1.getAttribute('aria-selected')).toBe('true')
        expect($tab2.getAttribute('aria-selected')).toBe('false')
        expect($tab3.getAttribute('aria-selected')).toBe('false')
        toggleTab($tab2, [$tab1, $tab3])
        expect($tab1.getAttribute('aria-selected')).toBe('false')
        expect($tab2.getAttribute('aria-selected')).toBe('true')
        expect($tab3.getAttribute('aria-selected')).toBe('false')
        toggleTab($tab3, [$tab1, $tab2])
        expect($tab1.getAttribute('aria-selected')).toBe('false')
        expect($tab2.getAttribute('aria-selected')).toBe('false')
        expect($tab3.getAttribute('aria-selected')).toBe('true')

    })
})

describe('pluralize', () => {

    test('return empty string for string "1"', () => {
        expect(pluralize('1')).toBe('')
    })

    test('returns "s" for other strings', () => {
        expect(pluralize('2')).toBe('s')
        expect(pluralize('0')).toBe('s')
        expect(pluralize('-324')).toBe('s')
        expect(pluralize('foo')).toBe('s')
    })

    test('return empty string for number 1', () => {
        expect(pluralize(1)).toBe('')
    })

    test('returns "s" for other numbers', () => {
        expect(pluralize(2)).toBe('s')
        expect(pluralize(0)).toBe('s')
        expect(pluralize(-324)).toBe('s')
    })

    test('return empty string for array of length 1', () => {
        expect(pluralize(['foo'])).toBe('')
    })

    test('returns "s" for other arrays', () => {
        expect(pluralize(['foo', 'bar'])).toBe('s')
        expect(pluralize([])).toBe('s')
    })
})