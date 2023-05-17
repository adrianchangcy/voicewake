<template>
    <div class="flex flex-row">
        <div class="flex flex-row">
            <span class="block text-3xl">{{ propEventTone.event_tone_symbol }}</span>
            <span class="sr-only">{{ propEventTone.event_tone_name }}</span>
            <div class="my-auto px-2">
                <span>
                    &#8213;
                </span>
            </div>
        </div>
        <div class="overflow-hidden text-ellipsis whitespace-nowrap my-auto text-theme-black shade-text-when-hover transition-colors duration-200 ease-in-out">
            <a href="yolo">
                <i class="fas fa-user text-lg"></i> <span class="text-sm">{{ propUsername }}</span>
            </a>
        </div>
    </div>
</template>


<script setup lang="ts">
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import EventToneTypes from '@/types/EventTones.interface';

    export default defineComponent({
        props: {
            propUsername: {
                type: String,
                default: ''
            },
            propEventTone: {
                type: Object as PropType<EventToneTypes>,
                default: null
            }
        }
    });
</script>