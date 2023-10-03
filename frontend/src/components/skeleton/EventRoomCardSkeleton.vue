<template>
    <div
        :class="[
            propHasBorder === true ? 'px-4 pt-8 pb-12      border border-theme-light-gray rounded-lg' : '',
            'flex flex-col'
        ]"
    >
        <span class="sr-only">loading events</span>
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
            <!--events-->
            <div v-for="x in propEventQuantity" :key="x">
                <VEventCardSkeleton/>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VEventCardSkeleton from './VEventCardSkeleton.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        props: {
            propHasBorder: {
                type: Boolean,
                default: false
            },
            propEventQuantity: {
                type: Number,
                default: 2
            },
        }
    });
</script>