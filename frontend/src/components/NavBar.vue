<template>
    <nav class="overflow-y-scroll scroll-smooth fixed top-0 w-full max-h-full py-5     text-left text-3xl leading-none      backdrop-blur bg-theme-light/40">
        <ul class="w-auto      grid grid-flow-row grid-cols-1 auto-rows-max gap-2 place-content-around">
            <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-5 items-center      grid grid-cols-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                    <i class="col-span-1    fas fa-wave-square"></i>
                </a>
            </li>
            <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-5 items-center       grid grid-cols-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20       shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                    <i class="col-span-1    fas fa-microphone-lines"></i>
                    <span class="col-span-2">Talk</span>
                </a>
            </li>
            <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-5 items-center      grid grid-cols-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20       shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                    <i class="col-span-1    fas fa-calendar-plus"></i>
                    <span class="col-span-2">Request</span>
                </a>
            </li>
            <!-- <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-5 items-center      grid grid-cols-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20       shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                    <i class="col-span-1    fa-solid fa-user"></i>
                    <span class="col-span-2">Sign In</span>
                </a>
            </li> -->

            <!--when signed in-->
            <Menu as="li" class="grid row-auto grid-flow-row" v-slot="{ open }">
                <div class="row-span-1 flex flex-nowrap z-10">
                    <MenuButton class="flex-1 mx-5 p-5 items-center     text-left     grid grid-cols-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                        <i class="col-span-1    fa-solid fa-user"></i>
                        <span class="col-span-2">Account</span>
                        <!--put transition here, and make it the same as the dropdown-->
                        <i :class='{
                            "col-span-1    text-right    fas fa-chevron-down opacity-0": !open,
                            "col-span-1    text-right    fas fa-chevron-down opacity-50": open,
                        }'
                        >
                        </i>
                    </MenuButton>
                </div>
                <div :class='{
                        "row-span-1 bg-theme-light/40 shadow-sm flex flex-nowrap z-0 text-left leading-none  w-auto mx-5 p-5 mt-2": open,
                    }'
                >
                    <MenuItems class="flex-1 gap-2 divide-y">
                        <MenuItem v-slot="{ active }" class="items-center p-2">
                            <a
                            :class="{
                                '': !active,
                                'bg-green-400': active,
                            }"
                            href="/"
                            class="grid grid-cols-4"
                            >
                                <i class="col-span-1    fas fa-microphone-lines"></i>
                                <span class="col-span-2">Past Talks</span>
                            </a>
                        </MenuItem>
                        <MenuItem v-slot="{ active }" class="items-center p-2">
                            <a
                            :class="{
                                '': !active,
                                '': active,
                            }"
                            href="/"
                            class="grid grid-cols-4"
                            >
                                <i class="col-span-1    fas fa-calendar"></i>
                                <span class="col-span-2">Past Requests</span>
                            </a>
                        </MenuItem>
                        <MenuItem v-slot="{ active }" class="items-center p-2">
                            <a
                            :class="{
                                '': !active,
                                '': active,
                            }"
                            href="/"
                            class="grid grid-cols-4"
                            >
                                <span class="1"></span>
                                <span class="col-span-2">can scroll? 1</span>
                            </a>
                        </MenuItem>
                        <MenuItem v-slot="{ active }" class="items-center p-2">
                            <a
                            :class="{
                                '': !active,
                                '': active,
                            }"
                            href="/"
                            class="grid grid-cols-4"
                            @hook:mounted="dodo"
                            >
                                <span class="1"></span>
                                <span class="col-span-2">can scroll? 2</span>
                            </a>
                        </MenuItem>
                    </MenuItems>
                </div>
            </Menu>
       

        </ul>
    </nav>
</template>


  
<script setup>
  
    import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';

</script>



        
