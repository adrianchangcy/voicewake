<template>
    <CreateEvents
        :propIsOriginator="true"
    />
</template>

<script setup lang="ts">
    import CreateEvents from '/src/components/main/CreateEvents.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';

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


