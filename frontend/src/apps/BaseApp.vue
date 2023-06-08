<template>
    <NavBar/>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';
    import NavBar from '/src/components/main/NavBar.vue';

    export default defineComponent({
        name: 'BaseApp',
        components: {
            NavBar,
        }
    });
</script>


