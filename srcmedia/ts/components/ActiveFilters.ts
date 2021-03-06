import { Component, unslugify } from '../lib/common'

type Filter = {
    type: 'boolean' | 'facet' | 'range',
    input: string,
    name: string,
    value: string,
}

export default class ActiveFilters extends Component {
    $form: HTMLFormElement         // form whose filters we want to track
    $inner: HTMLElement            // container for list of buttons
    $clearAll: HTMLAnchorElement   // 'clear all' button

    // inputs in a range filter or text facet fieldset have this pattern:
    // id_nationality_1, id_gender_10, etc.
    multiWidgetPattern: RegExp = /^(.*)_\d+$/

    constructor(element: HTMLElement) {
        super(element)

        // find the containing form and store
        const form = this.element.closest('form')
        if (!form) console.error('No containing form found')
        else this.$form = form

        // find the 'clear all' button and store
        const clearAll = this.element.querySelector('.clear-all')
        if (!clearAll) console.error('No .clear-all element found')
        else this.$clearAll = (clearAll as HTMLAnchorElement)

        // find the inner area where buttons are listed
        const inner = this.element.querySelector('.inner')
        if (!inner) console.error('No .inner element found')
        else this.$inner = (inner as HTMLElement)

        // turn all links currently inside the element into buttons w/ handlers
        const $anchors = this.$inner.querySelectorAll('a')
        $anchors.forEach(($anchor: HTMLAnchorElement) => {
            $anchor.removeAttribute('href')
            $anchor.setAttribute('role', 'button')
            this.bindClearHandler($anchor)
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
    protected bindClearHandler($button: HTMLAnchorElement): void {
        const inputId = $button.dataset.input
        const fieldsetId = $button.dataset.fieldset

        // ignore the clear-all button
        if ($button.classList.contains('clear-all')) return

        // if it's not the clear-all button, it should have an assoc. input or fieldset
        if (!inputId && !fieldsetId) {
            console.error('No associated input for filter button', $button.outerHTML)
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
            })
        }
    }

    /**
     * Handle events originating from the form itself, e.g. the user typing into
     * a range filter or clicking a checkbox.
     *
     * @param event form events
     */
    protected handleFormInput(event: InputEvent): void {
        const target = event.target as HTMLInputElement
        const idMatch = target.id.match(this.multiWidgetPattern) as RegExpMatchArray

        // determine the type of filter that is affected, then delegate to the
        // add(), remove(), or change() functions.

        // boolean filters and text facets
        if (target.type == 'checkbox') {

            let filter: Filter = {
                type: 'boolean',
                input: target.id,
                name: target.name,
                value: target.value
            }

            // text facets have ids that match the multiWidgetPattern
            if (idMatch) {
                filter.type = 'facet'

                // scrape the value from the content of the label, so that we
                // can handle null value cases like "Unidentified" correctly
                //@ts-ignore
                filter.value = target.labels[0].childNodes[0].textContent.trim()
            }

            if (target.checked) this.add(filter)   // checked = add new filter
            else this.remove(filter)               // unchecked = remove filter
        }

        // range filters
        else if (target.type == 'number') {
            
            // find both inputs via parent fieldset, generate inner text
            const $fieldset = document.getElementById(idMatch[1]) as HTMLFieldSetElement
            const [$rangeStart, $rangeStop]: HTMLInputElement[] = Array.from($fieldset.querySelectorAll('input'))
            const $legend = $fieldset.querySelector('legend') as HTMLLegendElement
            const buttonContent = `${$rangeStart.value} – ${$rangeStop.value}`
            const filter: Filter = {
                type: 'range',
                input: idMatch[1],  // fieldset id
                name: $legend.textContent as string,
                value: buttonContent
            }
            
            // if both inputs are empty, delete button
            if ($rangeStart.value == '' && $rangeStop.value == '')
                this.remove(filter)

            // otherwise create/update existing button
            else this.update(filter)
        }
    }

    /**
     * Generate the text that will appear on a filter's button, depending on
     * what type of filter was passed.
     *
     * @param filter
     */
    protected buttonText(filter: Filter) {
        switch(filter.type) {
            case 'range':
                // append the filter's name in addition to the range
                return `${filter.name}: ${filter.value}`
            case 'boolean':
                // unslugify the filter's name
                return unslugify(filter.name)
            case 'facet':
            default:
                // just use the value of the selected option
                return filter.value
        }
    }

    /**
     * Hide the active filters list and make it non-interactive.
     */
    protected hide(): void {
        this.element.classList.add('hidden')
        this.$clearAll.removeAttribute('tabindex')
    }

    /**
     * Show the active filters list and make it interactive.
     */
    protected show(): void {
        this.element.classList.remove('hidden')
        this.$clearAll.setAttribute('tabindex', '0')
    }

    /**
     * Create a new button for a provided filter and add it inside the element.
     * If the element was hidden, show it so the filter is visible.
     *
     * @param filter values to use for button
     */
    add(filter: Filter): void {
        // create the button element
        const $button = document.createElement('a')
        $button.setAttribute('role', 'button')
        $button.setAttribute('tabindex', '0')
        $button.textContent = this.buttonText(filter)
        if (filter.type == 'range')
            $button.dataset.fieldset = filter.input
        else
            $button.dataset.input = filter.input

        // bind click handler
        this.bindClearHandler($button)

        // add it to the inside of the element
        this.$inner.insertBefore($button, this.$clearAll)

        // make sure active filters are now showing
        this.show()
    }

    /**
     * Remove a filter's button. If there are no remaining active filters, hide
     * the entire element.
     *
     * @param filter filter to remove
     */
    remove(filter: { input: string; type: string }): void {
        let $button: HTMLAnchorElement

        // find the corresponding filter button
        if (filter.input && filter.type) {
            if (filter.type == 'range')
                $button = this.$inner.querySelector(`a[data-fieldset=${filter.input}`) as HTMLAnchorElement
            else
                $button = this.$inner.querySelector(`a[data-input=${filter.input}`) as HTMLAnchorElement
        }

        // remove the button and hide the element if it's now empty
        //@ts-ignore
        if ($button) $button.remove()
        if (this.count() == 0) this.hide()
    }

    /**
     * Update the text displayed on a filter's button. If the button doesn't
     * exist, create a new one instead.
     *
     * @param filter filter to update
     */
    update(filter: Filter): void {
        let $button: HTMLAnchorElement

        // find the corresponding button - if none exists, delegate to add()
        $button = this.$inner.querySelector(`a[data-fieldset=${filter.input}`) as HTMLAnchorElement
        if (!$button) return this.add(filter)

        // update the button's content
        $button.innerText = this.buttonText(filter)
    }

    /**
     * Check how many filters are active by counting the number of buttons
     * displayed inside the element.
     */
    count(): number {
        return this.$inner.querySelectorAll('a:not(.clear-all)').length
    }

    /**
     * Remove all active filters by "clicking" each button.
     */
    clearAll(): void {
        const $buttons = this.$inner.querySelectorAll('a:not(.clear-all)')
        $buttons.forEach($button => $button.dispatchEvent(new Event('click')))
    }
}