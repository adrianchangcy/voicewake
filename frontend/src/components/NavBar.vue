<template>
    <nav class="fixed top-0 w-full max-h-full p-2         text-left text-2xl text-black leading-none      backdrop-blur bg-theme-light/40">
        <ul class="w-full h-fit      text-center      grid grid-flow-col grid-rows-1 grid-cols-4 gap-2">
            <li class="col-span-1 flex flex-nowrap">
                <a href="/" aria-labelledby="home" class="flex-1 p-4      grid grid-rows-1 items-center      transition duration-100 ease-in-out hover:scale-95">
                    <i class="row-span-1 fas fa-wave-square"></i>
                </a>
            </li>
            <li class="col-span-1 flex flex-nowrap">
                <a href="/" aria-labelledby="talk" class="flex-1 p-4      grid grid-rows-1 items-center      border-l-2 border-t-2 border-white/50     bg-theme-light/60 shadow-md rounded-lg    hover:bg-theme-light/40 hover:shadow-sm transition duration-100 ease-in-out hover:scale-95">
                    <i class="col-span-1 fas fa-microphone-lines"></i>
                </a>
            </li>
            <li class="col-span-1 flex flex-nowrap">
                <a href="/" aria-labelledby="listen" class="flex-1 p-4      grid grid-rows-1 items-center      border-l-2 border-t-2 border-white/50     bg-theme-light/60 shadow-md rounded-lg    hover:bg-theme-light/40 hover:shadow-sm transition duration-100 ease-in-out hover:scale-95">
                    <i class="col-span-1 fas fa-ear-listen"></i>
                </a>
            </li>
            <Menu as="li" class="col-span-1 flex flex-nowrap" v-slot="{ open }">
                <MenuButton aria-labelledby="More options" class="flex-1 p-4      grid grid-rows-1 items-center      border-l-2 border-t-2 border-white/50     bg-theme-light/60 shadow-md rounded-lg    hover:bg-theme-light/40 hover:shadow-sm transition duration-100 ease-in-out hover:scale-95">
                    <div class="grid grid-rows-3 grid-flow-row      justify-items-center place-items-center">
                        <div
                            :class="[
                                open ? 'mb-0 rotate-45' : 'mb-4 rotate-0',
                                'row-span-1 bg-black absolute   w-6 h-1     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                open ? 'bg-black/0 translate-y-4' : 'bg-black/100 translate-y-0',
                                'row-span-1 absolute   w-6 h-1     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                open ? 'mb-0 -rotate-45' : 'mt-4 rotate-0',
                                'row-span-1 bg-black absolute   w-6 h-1     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                    </div>
                </MenuButton>
                <Transition
                    enter-from-class="transform scale-100 opacity-0 -translate-y-2"
                    enter-active-class="transition duration-200 ease-in-out"
                    enter-to-class="transform scale-100 opacity-100 translate-y-0"
                    leave-from-class="transform scale-100 opacity-100"
                    leave-active-class="transition duration-200 ease-in-out"
                    leave-to-class="transform scale-100 opacity-0 -translate-y-2"
                >
                <MenuItems as="div" class="flex-1       grid grid-flow-row gap-y-2 divide-y w-full     left-0 right-0 absolute mt-20">
                    <MenuItem v-slot="{ active }" class="flex flex-nowrap">
                        <a href="/"
                            :class="[
                                active ? 'shadow-sm scale-95' : 'shadow-lg scale-100',
                                'flex-1 p-4 items-center transition duration-200 ease-in-out'
                            ]"
                        >
                            <i class="col-span-1    fas fa-microphone-lines"></i>
                            <span class="col-span-2">Talk</span>
                        </a>
                    </MenuItem>
                </MenuItems>
                </Transition>
            </Menu>

        </ul>
    </nav>
</template>


  
<script setup>
  
    import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
</script>


<script>

    export default{
        data(){
            return {
            };
        },
    }
</script>



