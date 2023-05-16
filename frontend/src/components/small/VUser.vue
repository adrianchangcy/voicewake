<template>
    <div class="flex flex-row gap-2">
        <div class="overflow-hidden text-ellipsis whitespace-nowrap my-auto text-theme-black shade-text-when-hover transition-colors duration-200 ease-in-out">
            <a href="yolo">
                <i class="fas fa-user text-xl"></i> <span class="text-base">{{ propUsername }}</span>
            </a>
        </div>
        <div class="my-auto">
            <span>
                &#8213;
            </span>
        </div>
        <div>
            <span class="block text-3xl">{{ propEventToneSymbol }}</span>
        </div>
    </div>
</template>


<script setup lang="ts">
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        props: {
            propUsername: {
                type: String,
                default: ''
            },
            propEventToneSymbol: {
                type: String,
                default: ''
            },
            propEventToneName: {
                type: String,
                default: ''
            }
        }
    });
</script>