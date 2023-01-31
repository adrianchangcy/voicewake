<template>
    <ViewMainEvents/>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';
    import ViewMainEvents from '/src/components/main/ViewMainEvents.vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'ViewMainEventsApp',
        components: {
            ViewMainEvents,
        },
        methods: {
        }
    });
</script>


