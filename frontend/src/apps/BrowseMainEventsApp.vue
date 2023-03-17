<template>
    <BrowseMainEvents/>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';
    import BrowseMainEvents from '/src/components/main/BrowseMainEvents.vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'BrowseMainEventsApp',
        components: {
            BrowseMainEvents,
        },
        methods: {
        }
    });
</script>


