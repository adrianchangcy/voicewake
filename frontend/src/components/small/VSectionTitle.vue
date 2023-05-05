<template>
    <div class="w-fit h-fit pt-7 pb-8">
        <div class="w-fit h-fit text-4xl font-light text-theme-black">
            <span>{{propTitle}}</span>
        </div>
        <div class="w-fit h-fit text-2xl font-light text-theme-black/80 pt-2">
            <span>{{propTitleDescription}}</span>
        </div>
    </div>
</template>


<script>
    import { defineComponent } from 'vue';

    export default defineComponent({

        props: {
            propTitle: {
                type: String,
                default: ''
            },
            propTitleDescription: {
                type: String,
                default: ''
            },
        }
    });
</script>