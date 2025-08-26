<template>
    <!--py instead of pt pb like event, because no texts here to make dimensions irregular-->
    <div
        :class="[
            propHasBorder === true ? 'border-y border-theme-gray-1 dark:border-dark-theme-gray-1' : '',
            propHasPadding === true ? 'px-2 sm:px-4 pt-8 pb-11' : '',
            'flex flex-col'
        ]"
    >
        <span class="sr-only">loading audio clips</span>
        <!--title and datetime-->
        <!--<div> seems to have bigger height than the inner <span>, and doing it all in <span> didn't work-->
        <div class="flex flex-col pb-6">
            <div class="w-[75%] h-6 flex items-center">
                <div class="w-full h-5 rounded-lg skeleton"></div>
            </div>
            <div class="w-[25%] h-6 flex items-center">
                <div class="w-full h-5 rounded-lg skeleton"></div>
            </div>
        </div>
        <div class="flex flex-col gap-8">
            <!--audio-clips-->
            <div v-for="x in propAudioClipQuantity" :key="x">
                <VAudioClipCardSkeleton/>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VAudioClipCardSkeleton from './VAudioClipCardSkeleton.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        props: {
            propHasBorder: {
                type: Boolean,
                default: false
            },
            propHasPadding: {
                type: Boolean,
                default: false
            },
            propAudioClipQuantity: {
                type: Number,
                default: 2
            },
        }
    });
</script>