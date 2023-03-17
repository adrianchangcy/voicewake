<template>
    <ViewSpecificEvents/>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';
    import ViewSpecificEvents from '/src/components/main/ViewSpecificEvents.vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'ViewSpecificEventsApp',
        components: {
            ViewSpecificEvents,
        },
        methods: {
        }
    });
</script>


