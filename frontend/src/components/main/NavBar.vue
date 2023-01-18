<template>
    <nav class="text-center text-xl text-black leading-none">
        <div ref="nav_main" class="p-2 lg:px-8   flex flex-nowrap     backdrop-blur bg-theme-light/60 border-b border-black/5">
            <ul class="w-full      grid gap-2 grid-flow-col grid-rows-1 grid-cols-4 lg:grid-cols-10">
                <li class="col-span-1 flex flex-nowrap justify-center">
                    <a href="/" aria-label="home" class="flex-1 p-4 lg:p-2      grid items-center">
                        <i class="fas fa-wave-square"></i>
                    </a>
                </li>
                <li class="col-span-2 hidden lg:flex"></li>
                <li class="col-span-1 lg:col-span-2 flex flex-nowrap">
                    <VNavigationButton propElement="a" propUrl="/" class="w-full h-full p-4 lg:p-2">
                        <i class="fas fa-ear-listen"></i>
                        <span class="hidden lg:block">Hear</span>
                    </VNavigationButton>
                </li>
                <li class="col-span-1 lg:col-span-2 flex flex-nowrap">
                    <VNavigationButton propElement="a" propUrl="/" class="w-full h-full p-4 lg:p-2">
                        <i class="fas fa-quote-left"></i>
                        <span class="hidden lg:block">Say</span>
                    </VNavigationButton>
                </li>
                <li class="col-span-2 hidden lg:flex"></li>
                <li v-if="!is_logged_in" class="hidden lg:col-span-1 lg:flex flex-nowrap">
                    <VNavigationButton propElement="a" propUrl="/" class="w-full h-full p-4 lg:p-2">
                        <i class="fas fa-user"></i>
                        <span class="hidden lg:block">Login</span>
                    </VNavigationButton>
                </li>
                <li
                    :class="[
                        is_logged_in ? 'hidden lg:flex' : 'hidden',
                        'col-span-1 flex-nowrap justify-center'
                    ]"
                >
                    <div ref="nav_main_more_button">
                        <VActionButtonWeird
                            aria-label="more options"
                            @click="toggle_nav_main_more"
                            class="w-fit h-full p-4 lg:p-2"
                        >
                            <i class="fas fa-circle-user"></i>
                        </VActionButtonWeird>
                    </div>
                </li>
                <li ref="nav_main_more_mobile_button" class="col-span-1 flex flex-nowrap lg:hidden">
                    <VNavigationButton
                        propElement="button"
                        aria-label="more options"
                        @click="toggle_nav_main_more"
                        class="w-full h-full p-4 lg:p-2"
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
                    </VNavigationButton>
                </li>
            </ul>
        </div>
        <TransitionFade>
            <div 
                v-show="is_nav_main_more_open"
                v-click-outside="{
                    var_name_for_element_bool_status: 'is_nav_main_more_open',
                    refs_to_exclude: ['nav_main_more_button', 'nav_main_more_mobile_button']
                }"
                class="w-screen h-screen absolute right-0 lg:max-w-fit lg:border-l border-black/5      backdrop-blur bg-theme-light/60"
            >
                <div class="p-4 lg:p-8 overflow-y-auto">
                    <div v-if="is_logged_in" class="p-4 grid gap-y-2">
                        <i class="col-span-1 fas fa-circle-user text-4xl"></i>
                        <p>{{username}}</p>
                    </div>
                    <div v-if="is_logged_in" class="flex flex-nowrap flex-col gap-y-2">
                        <VNavigationButton propElement="a" propUrl="/" class="w-full h-full p-4 lg:p-2">
                            <div class="grid grid-cols-4 grid-flow-col">
                                <i class="col-span-1 fas fa-door-open"></i>
                                <span class="col-span-2">Logout</span>
                            </div>
                        </VNavigationButton>
                    </div>
                    <div v-else class="flex flex-nowrap flex-col gap-y-2">
                        <VNavigationButton propElement="button" class="w-full h-full p-4 lg:p-2">
                            <div class="grid grid-cols-4 grid-flow-col">
                                <i class="col-span-1 fas fa-user"></i>
                                <span class="col-span-2">Login</span>
                            </div>
                        </VNavigationButton>
                        <VNavigationButton propElement="button" class="w-full h-full p-4 lg:p-2">
                            <div class="grid grid-cols-4 grid-flow-col">
                                <i class="col-span-1 fas fa-right-to-bracket"></i>
                                <span class="col-span-2">Sign Up</span>
                            </div>
                        </VNavigationButton>
                    </div>
                </div>
            </div>
        </TransitionFade>
    </nav>
</template>

<script setup>

    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    import VNavigationButton from '/src/components/small/VNavigationButton.vue';
    import VActionButtonWeird from '/src/components/small/VActionButtonWeird.vue';
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
        components: {
            VNavigationButton,
            VActionButtonWeird
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



