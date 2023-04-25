<template>
    <CreateEvents
        :propIsOriginator="true"
    />
</template>


<script lang="ts">
    import { defineComponent } from 'vue';
    import CreateEvents from '/src/components/main/CreateEvents.vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'CreateEventRoomsApp',
        components: {
            CreateEvents,
        },
        methods: {
        }
    });
</script>


