<template>
    <div>
        <span class="sr-only">loading events</span>
        <!--title and datetime-->
        <div class="flex flex-col gap-1 pb-6">
            <div class="w-[75%] h-6 rounded-lg skeleton"></div>
            <div class="w-[25%] h-4 rounded-lg skeleton"></div>
        </div>
        <div class="flex flex-col gap-6">
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
            propEventQuantity: {
                type: Number,
                default: 2
            },
            propCanReply: {
                type: Boolean,
                default: false
            }
        }
    });
</script>