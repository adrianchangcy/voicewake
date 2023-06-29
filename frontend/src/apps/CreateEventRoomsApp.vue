<template>
    <VTitleXL class="py-10">
        <template #title>
            <div class="flex flex-col">
                <i class="fas fa-comment block text-2xl w-full text-center"></i>
                <span class="block w-full text-center">Start Event</span>
            </div>
        </template>
    </VTitleXL>
    <VCreateEvents
        :propIsOriginator="true"
    />
</template>

<script setup lang="ts">
    import VTitleXL from '@/components/small/VTitleXL.vue';
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


