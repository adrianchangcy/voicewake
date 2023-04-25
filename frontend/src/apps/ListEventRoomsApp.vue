<template>
    <ListEventRooms/>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';
    import ListEventRooms from '/src/components/main/ListEventRooms.vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'ListEventRoomsApp',
        components: {
            ListEventRooms,
        },
        methods: {
        }
    });
</script>


