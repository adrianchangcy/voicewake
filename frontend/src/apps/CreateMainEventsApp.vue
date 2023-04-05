<template>
    <CreateMainEvents
        :propIsOriginator="true"
    />
</template>


<script lang="ts">
    import { defineComponent } from 'vue';
    import CreateMainEvents from '/src/components/main/CreateMainEvents.vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'CreateMainEventsApp',
        components: {
            CreateMainEvents,
        },
        methods: {
        }
    });
</script>


