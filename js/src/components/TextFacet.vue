<script>
import FacetChoice from './FacetChoice.vue'

export default {
    components: {
        FacetChoice
    },
    props: {
        label: String,
        choices: Array,
    },
}
</script>

<template>
    <select multiple>
        <facet-choice
            v-for="choice in choices"
            :label="choice.label"
            :value="label + ':' + choice.label"
            :count="choice.count"
            :selected="choice.selected"
            :key="choice.label">
        </facet-choice>
    </select>
</template>

<style lang="scss">
select {
    width: 250px;
}
</style>