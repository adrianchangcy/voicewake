<template>
    <VTitle
        propFontSize="l"
        class="py-8"
    >
        <template #title>
            <div class="flex flex-col">
                <i class="fas fa-comment block text-2xl w-full text-center"></i>
                <span class="block w-full text-center">Start</span>
            </div>
        </template>
    </VTitle>
    <CreateEvents
        :propIsOriginator="true"
    />
</template>

<script setup lang="ts">
    import VTitle from '@/components/small/VTitle.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import CreateEvents from '/src/components/main/CreateEvents.vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'CreateEventRoomsApp',
        methods: {
        }
    });
</script>


