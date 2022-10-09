<template>
<nav class="fixed top-0 w-screen h-max-full    text-center text-xl xl:text-2xl text-black leading-none">
    <div ref="navMain" class="w-full h-fit p-2 lg:px-8   flex flex-nowrap     backdrop-blur bg-theme-light/60 border-b border-black/5">
        <ul class="w-full h-fit      grid gap-2 grid-flow-col grid-rows-1 grid-cols-4 lg:grid-cols-10">
            <li class="col-span-1 flex flex-nowrap">
                <a href="/" aria-labelledby="home" class="flex-1 p-4 lg:p-2      grid items-center">
                    <i class="fas fa-wave-square"></i>
                </a>
            </li>
            <li class="col-span-1 lg:col-span-2 flex flex-nowrap">
                <a href="/" aria-labelledby="talk" class="flex-1 p-4 lg:p-2      items-center      border-l-2 border-t-2 border-white/50     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out">
                    <i class="fas fa-microphone-lines"></i>
                    <span class="hidden lg:block">Talk</span>
                </a>
            </li>
            <li class="col-span-1 lg:col-span-2 flex flex-nowrap">
                <a href="/" aria-labelledby="listen" class="flex-1 p-4 lg:p-2      items-center      border-l-2 border-t-2 border-white/50     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out">
                    <i class="fas fa-ear-listen"></i>
                    <span class="hidden lg:block">Listen</span>
                </a>
            </li>
            <li v-if="is_logged_in" class="hidden lg:col-span-4 lg:flex">
            </li>
            <li v-else class="hidden lg:col-span-3 lg:flex">
            </li>
            <li v-if="!is_logged_in" class="hidden lg:col-span-1 lg:flex flex-nowrap">
                <a href="/" aria-labelledby="login" class="flex-1 p-4 lg:p-2      items-center      border-l-2 border-t-2 border-white/50     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out">
                    <i class="fas fa-user"></i>
                    <span class="hidden lg:block">Login</span>
                </a>
            </li>
            <li v-if="!is_logged_in" class="hidden lg:col-span-1 lg:flex flex-nowrap">
                <a href="/" aria-labelledby="sign up" class="flex-1 p-4 lg:p-2      items-center      border-l-2 border-t-2 border-white/50     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out">
                    <i class="fas fa-right-to-bracket"></i>
                    <span class="hidden lg:block">Sign Up</span>
                </a>
            </li>
            <li v-if="is_logged_in" class="hidden lg:col-span-1 lg:flex flex-nowrap">
                <button
                    ref="navMainMoreButton"
                    aria-labelledby="profile"
                    @click="toggle_nav_main_more"
                    class="flex-1 p-4 lg:p-2      items-center      border-l-2 border-t-2 border-white/50     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                >
                    <i class="fas fa-circle-user"></i>
                    <span class="block">{{username}}</span>
                </button>
            </li>
            <li class="col-span-1 flex flex-nowrap lg:hidden">
                <button
                    aria-labelledby="more options"
                    class="flex-1 p-4 lg:p-2      items-center      border-l-2 border-t-2 border-white/50     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                    @click="toggle_nav_main_more"
                >
                    <div class="grid grid-rows-3 grid-flow-row      justify-items-center place-items-center">
                        <div
                            :class="[
                                is_nav_main_more_open ? 'mb-0 rotate-45' : 'mb-4 rotate-0',
                                'row-span-1 bg-black/80 absolute   w-5 h-1     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                is_nav_main_more_open ? 'bg-black/0 translate-y-4' : 'bg-black/80 translate-y-0',
                                'row-span-1 absolute   w-5 h-1     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                is_nav_main_more_open ? 'mb-0 -rotate-45' : 'mt-4 rotate-0',
                                'row-span-1 bg-black/80 absolute   w-5 h-1     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                    </div>
                </button>
            </li>
        </ul>
    </div>
    <Transition
        enter-from-class="transform opacity-0"
        enter-active-class="transition duration-200 ease-in-out"
        enter-to-class="transform opacity-100"
        leave-from-class="transform opacity-100"
        leave-active-class="transition duration-200 ease-in-out"
        leave-to-class="transform opacity-0"
    >
        <div 
            v-if="is_nav_main_more_open"
            v-click-outside="{
                related_data: 'is_nav_main_more_open',
                exclude: 'navMainMoreButton'
            }"
            class="w-screen h-screen lg:absolute lg:max-w-fit lg:right-0 lg:border-l border-black/5      backdrop-blur bg-theme-light/60"
        >
            <div class="w-auto max-h-full p-4 lg:p-8 overflow-y-auto">
                <div v-if="is_logged_in" class="p-4 grid gap-y-2">
                    <i class="col-span-1 fas fa-circle-user text-4xl"></i>
                    <p>{{username}}</p>
                </div>
                <div v-if="is_logged_in" class="flex flex-nowrap flex-col gap-y-2">
                    <a
                        href="/"
                        class="flex-1 p-4 lg:p-2    items-center      grid grid-cols-4 grid-flow-col      border-l-2 border-t-2 border-white/50     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                    >
                        <i class="col-span-1 fas fa-door-open"></i>
                        <span class="col-span-2">Logout</span>
                    </a>
                </div>
                <div v-else class="flex flex-nowrap flex-col gap-y-2">
                    <a
                        href="/"
                        class="flex-1 p-4 lg:p-2    items-center      grid grid-cols-4 grid-flow-col      border-l-2 border-t-2 border-white/50     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                    >
                        <i class="col-span-1    fas fa-user"></i>
                        <span class="col-span-2">Login</span>
                    </a>
                    <a
                        href="/"
                        class="flex-1 p-4 lg:p-2    items-center      grid grid-cols-4 grid-flow-col      border-l-2 border-t-2 border-white/50     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                    >
                        <i class="col-span-1    fas fa-right-to-bracket"></i>
                        <span class="col-span-2">Sign Up</span>
                    </a>
                </div>
            </div>
        </div>
    </Transition>
    </nav>
</template>

  
<script setup>
  
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
</script>


<script>
    
    export default{
        data(){
            return {
                is_nav_main_more_open: false,
                is_logged_in: false,
                username: "",
            };
        },
        beforeMount(){

            //get username, is always string
            this.username = JSON.parse(document.getElementById('data-username').textContent);

            if(this.username !== ""){
                this.is_logged_in = true;
            }

            this.username="Adrian";
            this.is_logged_in = true;
        },
        methods: {
            toggle_nav_main_more(){

                this.is_nav_main_more_open = !this.is_nav_main_more_open;
            },
        },
    };




</script>



