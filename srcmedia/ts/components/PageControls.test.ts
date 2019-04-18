import PageControls from './PageControls'

beforeEach(() => {
    document.body.innerHTML = `<div id="page-controls"/>`
})

it('uses a `top` value of 0 by default', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const pc = new PageControls($el)
    expect(pc.top).toBe(0)
})

it('parses the `top` css property of its element if one is set', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    $el.style.top = '50px'
    const pc = new PageControls($el)
    expect(pc.top).toBe(50)
})

it('applies the `stuck` class when it reaches its top value', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const pc = new PageControls($el)
    // a stupid mock of window.requestAnimationFrame
    let handle:FrameRequestCallback = () => 0
    jest.spyOn(window, 'requestAnimationFrame').mockImplementation(cb => {
        handle = cb // store our scroll() handler
        return 0 // necessary because of FrameRequestCallback fn signature
    })
    // mock getBoundingClientRect so it looks like we're at our `top` value
    $el.getBoundingClientRect = jest.fn().mockImplementation(() => ({ top: 0 }))
    pc.scroll() // call scroll()
    handle(0) // fake requestAnimationFrame calling our handler
    expect(pc.element.classList.contains('stuck')).toBe(true)
})

it('removes the `stuck` class when not at its top value', () => {
    const $el = document.getElementById('page-controls') as HTMLDivElement
    const pc = new PageControls($el)
    let handle:FrameRequestCallback = () => 0
    jest.spyOn(window, 'requestAnimationFrame').mockImplementation(cb => {
        handle = cb
        return 0
    })
    // pretend we're at the top currently
    pc.element.classList.add('stuck')
    pc.stuck = true
    // fake scrolling away from the top
    $el.getBoundingClientRect = jest.fn().mockImplementation(() => ({ top: 250 }))
    pc.scroll()
    handle(0)
    expect(pc.element.classList.contains('stuck')).toBe(false)
})