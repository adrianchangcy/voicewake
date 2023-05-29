<template>
    <VSectionTitle>
        <template #title>
            <div class="flex flex-col">
                <i class="fas fa-comment block text-xl w-full text-center"></i>
                <span class="block w-full text-center">Start Event</span>
            </div>
        </template>
        <template #titleDescription>
            <span class="block w-full text-center">Say something nice</span>
        </template>
    </VSectionTitle>
    <VCreateEvents
        :propIsOriginator="true"
    />
</template>

<script setup lang="ts">
    import VSectionTitle from '@/components/small/VSectionTitle.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import VCreateEvents from '/src/components/medium/VCreateEvents.vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'CreateEventRoomsApp',
        components: {
            VCreateEvents,
        },
        methods: {
        }
    });
</script>


