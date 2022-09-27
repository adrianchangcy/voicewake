<template>
    <nav class="overflow-y-auto scroll-smooth fixed top-0 w-full max-h-full py-4    grid gap-2     text-left text-3xl leading-none      backdrop-blur bg-theme-light/40">
        <ul class="w-auto mx-5      text-center      grid grid-flow-col grid-cols-4 gap-2">
            <li class="col-span-2 flex flex-nowrap">
                <a href="/" class="flex-1 py-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-y-105">
                    <i class="align-middle fas fa-wave-square"></i>
                </a>
            </li>
            <li class="col-span-1">
            </li>
            <li class="col-span-1 flex flex-nowrap items-end">
                <button class="flex-1 py-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-y-105"
                    @click="toggle_full_nav"
                >
                    <div class="menu-btn    grid grid-rows-3 grid-flow-row" ref="menu_btn_ref">
                        <div class="menu-btn__burger-top        row-span-1"></div>
                        <div class="menu-btn__burger-middle     row-span-1"></div>
                        <div class="menu-btn__burger-bottom     row-span-1"></div>
                    </div>
                </button>
            </li>
        </ul>
        <ul v-if="is_full_nav" class="w-auto      grid grid-flow-row grid-cols-1 auto-rows-max gap-2">
            <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-4 items-center       grid grid-cols-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20       shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-y-105">
                    <i class="col-span-1    fas fa-microphone-lines"></i>
                    <span class="col-span-2">Talk</span>
                </a>
            </li>
            <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-4 items-center      grid grid-cols-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20       shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-y-105">
                    <i class="col-span-1    fas fa-calendar-plus"></i>
                    <span class="col-span-2">Request</span>
                </a>
            </li>
            <!-- <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-4 items-center      grid grid-cols-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20       shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-y-105">
                    <i class="col-span-1    fa-solid fa-user"></i>
                    <span class="col-span-2">Sign In</span>
                </a>
            </li> -->

            <!--when signed in-->
            <Menu as="li" class="grid row-auto grid-flow-row gap-2" v-slot="{ open }">
                <div class="row-span-1 flex flex-nowrap">
                    <MenuButton class="flex-1 mx-5 p-4 items-center     text-left     grid grid-cols-4      border-l-2 border-t-2 border-white/50 hover:border-white/70      hover:bg-theme-light/20      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-y-105">
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
                        "row-span-1 bg-theme-light/40 shadow-sm flex flex-nowrap text-left leading-none  w-auto mx-5 p-4": open,
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
                                <span class="col-span-2 text-clip">Past Talks</span>
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


<script>

    export default{
        data(){
            return {
                'is_full_nav': false,
            };
        },
        methods: {
            toggle_full_nav(){
                if(!this.is_full_nav){
                    this.$refs.menu_btn_ref.classList.add('open-full');
                }else{
                    this.$refs.menu_btn_ref.classList.remove('open-full');
                }
                this.is_full_nav = !this.is_full_nav;
            }
        }
    }
</script>

<style>
    .menu-btn__burger-middle {
    width: 50px;
    height: 6px;
    background: #fff;
    border-radius: 5px;
    transition: all .5s ease-in-out;
    }
    .menu-btn__burger-top,
    .menu-btn__burger-bottom {
    content: '';
    position: absolute;
    width: 50px;
    height: 6px;
    background: #fff;
    border-radius: 5px;
    transition: all .5s ease-in-out;
    }
    .menu-btn__burger-top {
    transform: translateY(-16px);
    }
    .menu-btn__burger-bottom {
    transform: translateY(16px);
    }
    /* ANIMATION */
    .menu-btn.open-full .menu-btn__burger-middle {
    transform: translateX(-50px);
    background: transparent;
    box-shadow: none;
    }
    .menu-btn.open-full .menu-btn__burger-top {
    transform: rotate(45deg);
    }
    .menu-btn.open-full .menu-btn__burger-bottom {
    transform: rotate(-45deg);
    }
</style>

      
