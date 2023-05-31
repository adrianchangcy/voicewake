<template>
    <component
        :is="propElement"
        class="
            border-t-2 border-theme-light-trim hover:border-theme-light-trim/40
            bg-theme-light/60 hover:bg-theme-light/80 rounded-2xl shadow-md hover:shadow-sm
            transition duration-150 ease-in-out
        "
    >
        <slot></slot>
    </component>
</template>

<script>
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {

            };
        },
        props: {
            propElement: String,
        }
    });
</script>