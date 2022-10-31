<template>
    <button
        class="items-center       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     bg-theme-light/60 hover:bg-theme-light/80 rounded-3xl shadow-md hover:shadow-sm    transition duration-150 ease-in-out hover:scale-[0.99]"
    >
        <slot></slot>
    </button>
</template>

<script>
    export default {
        data(){
            return {

            };
        },
    }
</script>