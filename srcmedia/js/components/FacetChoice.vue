<script>
export default {
    props: {
        label: String,
        value: String,
        count: Number,
        selected: Boolean,
    },
}
</script>

<template>
    <option :selected="selected" :value="value">
        <span class="label">{{ label }}</span>
        <span class="count">{{ count }}</span>
    </option>
</template>

<style lang="scss">
option {
    color: lightgreen;
}

::placeholder {
    color: gainsboro;
}
</style>
