import { Component } from '../lib/common'

type Filter = {
    type: 'boolean' | 'text' | 'range'
    input: string,
    name: string,
    value: string,
}

export default class ActiveFilters extends Component {
    $form: HTMLFormElement         // form whose filters we want to track
    $inner: HTMLElement            // container for list of buttons
    $legend: HTMLElement           // 'active filters' text
    $clearAll: HTMLAnchorElement   // 'clear all' button

    constructor(element: HTMLElement) {
        super(element)

        // find the containing form and store
        const form = this.element.closest('form')
        if (!form) console.error(`No containing form found for ${element}`)
        else this.$form = form

        // find the legend and store
        const legend = this.element.querySelector('.legend')
        if (!legend) console.error(`No .legend element found in ${element}`)
        else this.$legend = (legend as HTMLElement)

        // find the 'clear all' button and store
        const clearAll = this.element.querySelector('.clear-all')
        if (!clearAll) console.error(`No .clear-all element found in ${element}`)
        else this.$clearAll = (clearAll as HTMLAnchorElement)

        // find the inner area where buttons are listed
        const inner = this.element.querySelector('.inner')
        if (!inner) console.error(`No .inner element found in ${element}`)
        else this.$inner = (inner as HTMLElement)

        // turn all links currently inside the element into buttons w/ handlers
        const $anchors = this.element.querySelectorAll('a')
        $anchors.forEach(($anchor: HTMLAnchorElement) => {
            $anchor.removeAttribute('href')
            $anchor.setAttribute('role', 'button')
            ActiveFilters.bindClearHandler($anchor)
        })

        // add a special handler to the "clear all" button
        this.$clearAll.addEventListener('click', this.clearAll.bind(this))

        // listen to input events on the form to know when to redraw buttons
        this.$form.addEventListener('input', this.handleFormInput.bind(this))
    }

    /**
     * Given an anchor element (in this case we use <a> as buttons), binds a
     * click handler that clears the input whose id is stored in the data-input
     * attribute of the anchor element.
     * 
     * Handler clears the provided input element, either by untoggling or 
     * removing its current value. Dispatches the appropriate event as though
     * the user had cleared it manually.
     * 
     * @param $button 
     */
    static bindClearHandler($button: HTMLAnchorElement): void {
        const inputId = $button.dataset.input
        const fieldsetId = $button.dataset.fieldset

        // ignore the clear-all button
        if ($button.classList.contains('clear-all')) return

        // if it's not the clear-all button, it should have an assoc. input or fieldset
        if (!inputId && !fieldsetId) {
            console.error('No associated input for filter button', $button)
            return
        }

        // if it has a data-fieldset, it corresponds to two inputs (range)
        if (fieldsetId) {
            const $fieldset = document.getElementById(fieldsetId) as HTMLFieldSetElement
            
            if (!$fieldset) {
                console.error(`Couldn't find fieldset #${fieldsetId}`)
                return
            }

            // when clicked, clear out all the inputs and then fake an input event
            const $inputs = $fieldset.querySelectorAll('input')
            $button.addEventListener('click', () => {
                $inputs.forEach($input => {
                    $input.value = ''
                    $input.dispatchEvent(new Event('input', { bubbles: true }))
                })
                this.removeFilter($button)
            })
        }

        // otherwise it's a single checkbox (boolean or text facet)
        else {
            const $input = document.getElementById((inputId as string)) as HTMLInputElement

            if (!$input) {
                console.error(`Couldn't find input #${inputId}`)
                return
            }

            // for checkboxes we need to fake both change and input events
            $button.addEventListener('click', () => {
                $input.checked = false
                $input.dispatchEvent(new Event('change', { bubbles: true }))
                $input.dispatchEvent(new Event('input', { bubbles: true }))
                this.removeFilter($button)
            })
        }
    }

    /**
     * Remove all active filters by "clicking" each button.
     */
    protected clearAll(): void {
        const $buttons = this.$inner.querySelectorAll('a:not(.clear-all)')
        $buttons.forEach($button => $button.dispatchEvent(new Event('click')))
    }

    protected handleFormInput(event: Event): void {
        const target = event.target as HTMLInputElement
        if (target.type == 'checkbox') {
            if (target.checked) {
                this.add({
                    type: 'text',
                    input: target.id,
                    name: target.name,
                    value: target.value
                })
            }
            else {
                const $button = this.$inner.querySelector(`a[data-input=${target.id}`) as HTMLAnchorElement
                if ($button) this.removeFilter($button)
            }
        }
        else {
            if (target.value != '') {
                this.add({
                    type: 'range',
                    input: target.id,
                    name: target.name,
                    value: target.value
                })
            }
            else {
                // const $button = 
            }
        }
    }

    /**
     * Create a new button for a provided filter and add it inside the element.
     * 
     * @param filter values to use for button
     */
    add(filter: Filter): void {
        // create the button element
        const $button = document.createElement('a')
        $button.setAttribute('role', 'button')
        $button.innerText = filter.value
        $button.dataset.input = filter.input

        // bind click handler
        ActiveFilters.bindClearHandler($button)

        // add it to the inside of the element
        this.$inner.appendChild($button)

        // make sure active filters are now showing
        this.element.classList.remove('hidden')
    }

    public removeFilter($button: HTMLAnchorElement): void {
        $button.remove()
        if (this.count() == 0) this.element.classList.add('hidden')
    }

    update(id: string, filter: Filter): void {
        
    }

    contains(id: string) {

    }

    /**
     * Check how many filters are active by counting the number of buttons
     * displayed inside the element.
     */
    count(): number {
        return this.$inner.querySelectorAll('a:not(.clear-all)').length
    }
}