<template>
    <NavBar/>

    <svg
        width="40"
        height="40"
        viewBox="0 0 167.5 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        class="stroke-theme-black stroke-[6px]"
    >
    <line y1="-0.5" x2="80" y2="-0.5" transform="matrix(-0.344302 -0.938859 0.905771 -0.423768 48.5441 88)"/>
    <line y1="-0.5" x2="40" y2="-0.5" transform="matrix(-0.344302 -0.938859 0.905771 -0.423768 115 88)"/>
    <line y1="-0.5" x2="80" y2="-0.5" transform="matrix(0.344302 -0.938859 0.905771 0.423768 68 88.6281)"/>
    <line y1="-0.5" x2="40" y2="-0.5" transform="matrix(0.344302 -0.938859 0.905771 0.423768 134 88.314)"/>
    <line x1="48" y1="87.5" x2="68" y2="87.5"/>
    <line x1="114" y1="87.5" x2="134" y2="87.5"/>
    <line x1="81.5" y1="50.5" x2="101.5" y2="50.5"/>
    <line x1="14" y1="50.5" x2="34" y2="50.5"/>
    <line x1="1" y1="13.5" x2="21" y2="13.5"/>
    <line x1="94.5" y1="13.5" x2="114.5" y2="13.5"/>
    <line x1="146.5" y1="50.5" x2="166.5" y2="50.5"/>
    <circle cx="156.5" cy="14" r="10" class="stroke-none fill-theme-lead"/>
    </svg>
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


