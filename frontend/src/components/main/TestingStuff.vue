<template>
    <div
        :class="is_testing ? 'w-full h-screen items-center flex gap-10' : 'w-0 h-0'"
    >
    </div>
</template>


<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    // import anime from 'animejs';

    export default defineComponent({
        data(){
            return {
                is_testing: false,
            };
        },
    });
</script>