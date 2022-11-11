<template>
    <button
        class="
            h-20
            items-center       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40 
            bg-theme-light/60 hover:bg-theme-light/80 rounded-lg shadow-md hover:shadow-sm 
            transition duration-150 ease-in-out hover:scale-[0.99]
        "
    >
        <slot></slot>
    </button>
</template>


<script>
//focus:border-2 focus:outline-none focus:ring-1 focus:ring-theme-black focus:border-theme-black
    export default {
        data(){
            return {

            };
        },
    }
</script>