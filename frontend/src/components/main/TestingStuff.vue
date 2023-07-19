<template>
    <div
        :class="is_testing ? 'w-full h-screen items-center flex flex-col mt-10' : 'hidden'"
    >






    </div>
</template>


<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from 'notiwind';
    // import anime from 'animejs';

    export default defineComponent({
        data(){
            return {
                is_testing: false,
                notifications: [] as any[],
            };
        },
        mounted(){

            notify({
                title: "Keep it up!",
                text: "You'll finish this project soon. You can do this!",
                type: "ok"
            }, 3000);
        },
    });
</script>