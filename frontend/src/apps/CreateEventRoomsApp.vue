<template>
    <VCreateEvents
        :propIsOriginator="true"
    />
</template>


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


