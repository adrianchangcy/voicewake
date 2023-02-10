<template>

    <div class="text-theme-black text-2xl py-1 grid grid-cols-5">

        <div v-if="propIsSelected === false" class="col-span-4 h-20 border border-theme-light-gray bg-theme-light rounded-lg relative"></div>

        <button v-else class="col-span-4 h-20 border-2 border-dashed border-solid-when-hover border-theme-lead bg-theme-light rounded-lg relative" type="button">
            <span class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">
                Reply
            </span>
        </button>

    </div>
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


