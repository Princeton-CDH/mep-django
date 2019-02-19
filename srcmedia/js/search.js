import Vue from 'vue'

import TextFacet from './components/TextFacet'

const searchInstance = new Vue({
    components: {
        TextFacet,
    },
})

document.addEventListener('DOMContentLoaded', () => {
    console.log('search loaded')
})
