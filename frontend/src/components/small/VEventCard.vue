<template>

    <div class="text-theme-black">

        <!--username-->
        <div class="h-fit text-base font-extralight">
            <span><i class="fas fa-user"></i> {{propUsername}}</span>
        </div>
    
        <!--label, ripples, total duration-->
        <div class="py-1 grid grid-cols-5">
            <div class="col-span-4">
                <VActionButtonMedium
                    class="w-full grid grid-cols-7 gap-2"
                    @click.stop="handleIsSelected()"
                >
                    <!--label-->
                    <div class="col-span-2 col-start-1 h-full relative text-3xl">
                        <span
                            class="w-fit h-fit absolute left-0.5 right-0 top-0 bottom-0.5 m-auto"
                            :aria-label="event_tone_name"
                        >
                            {{event_tone_symbol}}
                        </span>
                    </div>
            
                    <!--ripples-->
                    <div class="col-span-3 col-start-3 h-[75%] top-0 bottom-0 my-auto relative">
                        <div
                            ref="volume_ripples_container"
                            class="w-full h-full absolute flex flex-row justify-between"
                        >
                            <div
                                v-for="volume_ripple in buckets.length" :key="volume_ripple"
                                ref="volume_ripple"
                                class="h-full scale-y-0 origin-center"
                            >
                                <div class="left-0 right-0 mx-auto w-0.5 h-full bg-theme-black">
                                </div>
                            </div>
                        </div>
                    </div>
            
                    <!--total duration, check icon for selected-->
                    <div class="col-span-2 col-start-6 h-full relative">
                        <div
                            v-if="propIsSelected === false"
                            class="w-full h-full absolute flex flex-row"
                        >
                            <span class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto text-sm">{{pretty_file_duration}}</span>
                        </div>
                        <i v-else class="absolute w-fit h-fit text-2xl fas fa-square-check text-theme-lead left-0 right-0 top-0 bottom-0 m-auto"></i>
                    </div>
                </VActionButtonMedium>
            </div>

            <div
                class="col-start-5 col-span-1 h-20 text-xl pl-1 md:pl-2"
            >
                <button
                    @click.stop="handleLiked()"
                    class="block w-full h-10 rounded-lg shade-when-hover transition-colors duration-200 ease-in-out relative"
                    type="button"
                >
                    <i
                        :class="[
                            is_liked === true ? 'text-theme-lead' : 'text-theme-lead/0',
                            'absolute w-fit h-fit fas fa-thumbs-up left-0 right-0 top-1 bottom-0 m-auto transition-colors duration-200 ease-in-out'
                        ]"
                    ></i>
                    <i class="absolute w-fit h-fit far fa-thumbs-up left-0 right-0 top-1 bottom-0 m-auto"></i>
                </button>
                <button
                    @click.stop="handleDisliked()"
                    class="block w-full h-10 rounded-lg shade-when-hover transition-colors duration-200 ease-in-out relative"
                    type="button"
                >
                    <i
                        :class="[
                            is_liked === false ? 'text-theme-lead' : 'text-theme-lead/0',
                            'absolute w-fit h-fit fas fa-thumbs-down left-0 right-0 top-1 bottom-0 m-auto transition-colors duration-200 ease-in-out'
                        ]"
                    ></i>
                    <i class="absolute w-fit h-fit far fa-thumbs-down left-0 right-0 top-1 bottom-0 m-auto"></i>
                </button>
            </div>
        </div>
    </div>
</template>


<script setup>

    import VActionButtonMedium from '/src/components/small/VActionButtonMedium.vue';
</script>


<script>
    // import anime from 'animejs';

    export default {
        data(){
            return {
                username: 'carlj101',
                event_tone_name: 'laugh cry',
                event_tone_symbol: '😭',
                buckets: [0.4, 0.2, 0.6, 0.7, 0.5, 0.2, 0.1, 0.7, 1, 1, 0.4, 0.2, 0.6, 0.7, 0.5, 0.2, 0.1, 0.7, 0.9, 0.9],
                pretty_file_duration: '01:20',
                pretty_upload_datetime: '40 minutes ago',
                is_liked: null,

            };
        },
        components: {
            VActionButtonMedium,
        },
        mounted(){

            for(let x = 0; x < this.buckets.length; x++){

                this.$refs.volume_ripple[x].style.transform = 'scaleY('+this.buckets[x]+')';
            }
        },
        props: {
            propUsername: {
                type: String,
                default: '',
            },
            propIsReply: {
                type: Boolean,
                default: false,
            },
            propIsSelected: {
                type: Boolean,
                default: false,
            },
        },

        methods: {
            handleIsSelected() {

                this.$emit('isSelected', true);
            },
            handleLiked() {

                console.log('liked!');
                if(this.is_liked === null || this.is_liked === false){

                    this.is_liked = true;

                }else{

                    this.is_liked = null;
                }
            },

            handleDisliked() {
                console.log('disliked!');
                if(this.is_liked === null || this.is_liked === true){

                    this.is_liked = false;

                }else{

                    this.is_liked = null;
                }
            }
        }

    }
</script>