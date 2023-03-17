<template>
    <button
        :class="[
            propIsSelected ? 'border-2 border-dashed border-solid-when-hover border-theme-lead' : 'border border-theme-light-gray cursor-default',
            'h-20 text-theme-black relative bg-theme-light rounded-lg transition-colors duration-150 ease-in-out'
        ]"
        type="button"
    >
        <span
            :class="[
                propIsSelected ? 'visible opacity-100' : 'invisible opacity-0',
                'w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto text-2xl transition-opacity duration-150 ease-in-out'
            ]"
        >
            Reply
        </span>
    </button>
</template>


<script>

    export default {

        data(){
            return {

            };
        },

        props:{
            propIsSelected: {
                type: Boolean,
                default: false,
            },
        }
    }
</script>


