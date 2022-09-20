<template>
    <nav class="sticky top-0 w-auto h-auto py-5     text-left text-2xl leading-none      backdrop-blur bg-gradient-to-r from-theme-light/40 via-theme-light/100 to-theme-light/40">
        <ul class="w-auto      grid grid-flow-row grid-cols-1 auto-rows-max gap-2 place-content-around">
            <li class="flex flex-nowrap">
                <a href="/" class="flex-1  mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                    <i class="col-span-1    fas fa-wave-square"></i>
                </a>
            </li>
            <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                    <i class="col-span-1    fas fa-microphone-lines"></i>
                    <span class="col-span-2">Talk</span>
                </a>
            </li>
            <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                    <i class="col-span-1    fas fa-calendar-plus"></i>
                    <span class="col-span-2">Request</span>
                </a>
            </li>
            <li class="flex flex-nowrap">
                <a class="flex-1 mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                    <span class="col-span-1"></span>
                    <span class="col-span-2">More</span>
                    <i class="col-span-1    text-right    fas fa-chevron-down opacity-50"></i>
                </a>  
            </li>
            <li class="flex flex-nowrap">
                <div id="nav-more" class="flex-1">
                    <ul class="w-auto      grid grid-flow-row grid-cols-1 auto-rows-max gap-2 place-content-around">
                        <li class="flex flex-nowrap">
                            <a class="flex-1 mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                                <i class="col-span-1    fas fa-microphone-lines"></i>
                                <span class="col-span-2">Past Talks</span>
                            </a>
                        </li>
                        <li class="flex flex-nowrap">
                            <a class="flex-1 mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                                <i class="col-span-1    fas fa-calendar"></i>
                                <span class="col-span-2">Past Requests</span>
                            </a>
                        </li>
                        <li class="flex flex-nowrap">
                            <a class="flex-1 mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                                <i class="col-span-1    fas fa-calendar"></i>
                                <span class="col-span-2">Past Requests</span>
                            </a>
                        </li>
                        <li class="flex flex-nowrap">
                            <a class="flex-1 mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                                <i class="col-span-1    fas fa-calendar"></i>
                                <span class="col-span-2">Past Requests</span>
                            </a>
                        </li>
                        <li class="flex flex-nowrap">
                            <a class="flex-1 mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                                <i class="col-span-1    fas fa-calendar"></i>
                                <span class="col-span-2">Past Requests</span>
                            </a>
                        </li>
                    </ul>
                </div>
            </li>
            <li class="flex flex-nowrap">
                <a href="/" class="flex-1 mx-5 p-5      grid grid-cols-4      border-l-2 border-t-2 border-white      shadow-md hover:shadow-lg transition duration-100 ease-in-out hover:translate-x-1 hover:translate-y-1 rounded-lg hover:scale-105">
                    <i class="col-span-1    fa-solid fa-user"></i>
                    <!--<i class="fas fa-door-open"></i>-->
                    <span class="col-span-2">Sign In</span>
                    <i class="col-span-1    text-right    fas fa-chevron-down opacity-50"></i>
                </a>
            </li>
        </ul>
    </nav>
</template>

<script>
    export default {
        data(){
            return{

            };
        },
        name: 'NavBar',
        props: {
          msg: String
        }
    };
</script>