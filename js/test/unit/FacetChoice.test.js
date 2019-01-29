import { mount } from '@vue/test-utils'

import FacetChoice from '../../src/components/FacetChoice'

describe('FacetChoice', () => {

    const wrapper = mount(FacetChoice, {
        propsData: {
            label: 'hemingway',
            value: 'author:hemingway',
            count: 55,
            selected: false,
        }
    })

    it('renders with label', () => {
        expect(wrapper.html()).toContain('<span class="label">hemingway</span>')
    })

    it('renders with count', () => {
        expect(wrapper.html()).toContain('<span class="count">55</span>')
    })
})