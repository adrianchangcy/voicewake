<template>
    <div
        :class="[
            propHasBorder === true ? 'px-4 pt-8 pb-12      border border-theme-light-gray rounded-lg' : '',
            'flex flex-col'
        ]"
    >
        <span class="sr-only">loading audio_clips</span>
        <!--title and datetime-->
        <!--<div> seems to have bigger height than the inner <span>, and doing it all in <span> didn't work-->
        <div class="flex flex-col pb-10">
            <div class="w-[75%] h-6 flex items-center">
                <div class="w-full h-5 rounded-lg skeleton"></div>
            </div>
            <div class="w-[25%] h-6 flex items-center">
                <div class="w-full h-5 rounded-lg skeleton"></div>
            </div>
        </div>
        <div class="flex flex-col gap-10">
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
            propAudioClipQuantity: {
                type: Number,
                default: 2
            },
        }
    });
</script>