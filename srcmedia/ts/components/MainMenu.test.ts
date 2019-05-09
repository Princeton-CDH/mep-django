import MainMenu from './MainMenu'

beforeEach(() => {
    document.body.innerHTML = `<ul id="main-menu"></ul>`
})

it('keeps a reference to its element', () => {
    let element = document.getElementById('main-menu') as HTMLElement
    const mm = new MainMenu(element)
    expect(mm.element).toBe(element)
})

it('prevents default link click event when shown', () => {
    let element = document.getElementById('main-menu') as HTMLElement
    let event = new MouseEvent('click')
    let mockPreventDefault = jest.fn()
    event.preventDefault = mockPreventDefault
    const mm = new MainMenu(element)
    return mm.show(event).then(() => {
        expect(mockPreventDefault.mock.calls.length).toBe(1)
    })
})

it('prevents default link click event when hidden', () => {
    let element = document.getElementById('main-menu') as HTMLElement
    let event = new MouseEvent('click')
    let mockPreventDefault = jest.fn()
    event.preventDefault = mockPreventDefault
    const mm = new MainMenu(element)
    return mm.hide(event).then(() => {
        expect(mockPreventDefault.mock.calls.length).toBe(1)
    })
})

it('shows itself when show() is called', () => {
    let element = document.getElementById('main-menu') as HTMLElement
    let event = new MouseEvent('click')
    const mm = new MainMenu(element)
    return mm.show(event).then(() => {
        expect(element.style.zIndex).toBe('100')
        expect(element.style.opacity).toBe('1')
        expect(element.style.pointerEvents).toBe('all')
    })
})

it('prevents scrolling when open', () => {
    let element = document.getElementById('main-menu') as HTMLElement
    let event = new MouseEvent('click')
    const mm = new MainMenu(element)
    return mm.show(event).then(() => {
        expect(document.body.style.overflowY).toBe('hidden')
    })
})

it('hides itself when hide() is called', () => {
    let element = document.getElementById('main-menu') as HTMLElement
    let event = new MouseEvent('click')
    const mm = new MainMenu(element)
    return mm.hide(event).then(() => {
        expect(element.style.zIndex).toBe('-100')
        expect(element.style.opacity).toBe('0')
        expect(element.style.pointerEvents).toBe('none')
    })
})

it('allows scrolling when closed', () => {
    let element = document.getElementById('main-menu') as HTMLElement
    let event = new MouseEvent('click')
    const mm = new MainMenu(element)
    return mm.hide(event).then(() => {
        expect(document.body.style.overflowY).not.toBe('hidden')
    })
})