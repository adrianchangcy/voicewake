<template>
    <GetEventRooms/>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';
    import GetEventRooms from '/src/components/main/GetEventRooms.vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'GetEventRoomsApp',
        components: {
            GetEventRooms,
        },
        methods: {
        }
    });
</script>


