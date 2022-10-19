<template>
    <nav class="text-center text-xl xl:text-2xl text-black leading-none">
        <div ref="navMain" class="p-2 lg:px-8   flex flex-nowrap     backdrop-blur bg-theme-light/60 border-b border-black/5">
            <ul class="w-full      grid gap-2 grid-flow-col grid-rows-1 grid-cols-4 lg:grid-cols-10">
                <li class="col-span-1 flex flex-nowrap justify-center">
                    <a href="/" aria-label="home" class="flex-1 p-4 lg:p-2      grid items-center">
                        <i class="fas fa-wave-square"></i>
                    </a>
                </li>
                <li class="col-span-1 lg:col-span-2 flex flex-nowrap">
                    <a href="/" class="flex-1 p-4 lg:p-2      items-center       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out">
                        <i class="fas fa-ear-listen"></i>
                        <span class="hidden lg:block">Hear</span>
                    </a>
                </li>
                <li class="col-span-1 lg:col-span-2 flex flex-nowrap">
                    <a href="/" class="flex-1 p-4 lg:p-2      items-center       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out">
                        <i class="fas fa-microphone-lines"></i>
                        <span class="hidden lg:block">Say</span>
                    </a>
                </li>
                <li :class="[
                    is_logged_in ? 'col-span-4' : 'col-span-3',
                    'hidden lg:flex'
                ]">
                </li>
                <li v-if="!is_logged_in" class="hidden lg:col-span-1 lg:flex flex-nowrap">
                    <a href="/" class="flex-1 p-4 lg:p-2      items-center       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out">
                        <i class="fas fa-user"></i>
                        <span class="hidden lg:block">Login</span>
                    </a>
                </li>
                <li v-if="!is_logged_in" class="hidden lg:col-span-1 lg:flex flex-nowrap">
                    <a href="/" class="flex-1 p-4 lg:p-2      items-center       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out">
                        <i class="fas fa-right-to-bracket"></i>
                        <span class="hidden lg:block">Sign Up</span>
                    </a>
                </li>
                <li v-if="is_logged_in" class="col-span-2 hidden lg:flex flex-nowrap justify-center">
                    <button
                        ref="nav_main_more_button"
                        aria-label="more options"
                        @click="toggle_nav_main_more"
                        class="flex-none p-4 lg:p-2      items-center       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     hover:bg-theme-light/80 shadow-md rounded-full    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                    >
                        <i class="fas fa-circle-user"></i>
                    </button>
                </li>
                <li class="col-span-1 flex flex-nowrap lg:hidden">
                    <button
                        ref="nav_main_more_mobile_button"
                        aria-label="more options"
                        class="flex-1 p-4 lg:p-2      items-center       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                        @click="toggle_nav_main_more"
                    >
                        <div class="grid grid-rows-3 grid-flow-row      justify-items-center place-items-center">
                            <div
                                :class="[
                                    is_nav_main_more_open ? 'mb-0 rotate-45' : 'mb-4 rotate-0',
                                    'row-span-1 bg-theme-black absolute   w-5 h-1     transition-all duration-200 ease-in-out',
                                ]"
                            >
                            </div>
                            <div
                                :class="[
                                    is_nav_main_more_open ? 'opacity-0' : 'opacity-100',
                                    'row-span-1 bg-theme-black absolute   w-5 h-1     transition-opacity duration-200 ease-in-out',
                                ]"
                            >
                            </div>
                            <div
                                :class="[
                                    is_nav_main_more_open ? 'mt-0 -rotate-45' : 'mt-4 rotate-0',
                                    'row-span-1 bg-theme-black absolute   w-5 h-1     transition-all duration-200 ease-in-out',
                                ]"
                            >
                            </div>
                        </div>
                    </button>
                </li>
            </ul>
        </div>
        <TransitionFade>
            <div 
                v-show="is_nav_main_more_open"
                v-click-outside="{
                    related_data: 'is_nav_main_more_open',
                    exclude: ['nav_main_more_button', 'nav_main_more_mobile_button']
                }"
                class="w-screen h-screen absolute right-0 lg:max-w-fit lg:border-l border-black/5      backdrop-blur bg-theme-light/60"
            >
                <div class="p-4 lg:p-8 overflow-y-auto">
                    <div v-if="is_logged_in" class="p-4 grid gap-y-2">
                        <i class="col-span-1 fas fa-circle-user text-4xl"></i>
                        <p>{{username}}</p>
                    </div>
                    <div v-if="is_logged_in" class="flex flex-nowrap flex-col gap-y-2">
                        <a
                            href="/"
                            class="flex-1 p-4 lg:p-2    items-center      grid grid-cols-4 grid-flow-col       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                        >
                            <i class="col-span-1 fas fa-door-open"></i>
                            <span class="col-span-2">Logout</span>
                        </a>
                    </div>
                    <div v-else class="flex flex-nowrap flex-col gap-y-2">
                        <a
                            href="/"
                            class="flex-1 p-4 lg:p-2    items-center      grid grid-cols-4 grid-flow-col       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                        >
                            <i class="col-span-1    fas fa-user"></i>
                            <span class="col-span-2">Login</span>
                        </a>
                        <a
                            href="/"
                            class="flex-1 p-4 lg:p-2    items-center      grid grid-cols-4 grid-flow-col       border-t-2 border-theme-light-trim hover:border-theme-light-trim/40     hover:bg-theme-light/80 shadow-md rounded-lg    bg-theme-light/60 hover:shadow-sm transition duration-150 ease-in-out"
                        >
                            <i class="col-span-1    fas fa-right-to-bracket"></i>
                            <span class="col-span-2">Sign Up</span>
                        </a>
                    </div>
                </div>
            </div>
        </TransitionFade>
    </nav>
</template>

  
<script setup>
  
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    import TransitionFade from '/src/transitions/TransitionFade.vue';
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

            this.username="Adrian1111111111";
            this.is_logged_in = true;
        },
        methods: {
            toggle_nav_main_more(){

                this.is_nav_main_more_open = !this.is_nav_main_more_open;
            },
        },
    };




</script>



