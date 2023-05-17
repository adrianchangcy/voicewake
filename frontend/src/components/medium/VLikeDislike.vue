<template>
    <div class="h-10 text-xl">
        <div class="w-full h-full grid grid-cols-2 gap-0.5">
            <!--like-->
            <button
                ref="like_button"
                @click.stop="handleLiked()"
                class="col-span-1 h-full px-5 flex flex-row bg-theme-light/60    hover:bg-theme-light/80 hover:border-theme-light-trim/40 hover:shadow-sm       border-t-2 border-theme-light-trim rounded-full rounded-r-none shadow-md transition duration-150 ease-in-out"
                type="button"
            >
                <!--like button-->
                <div
                    class="w-6 h-full relative"
                    ref="like_logo"
                >
                    <i
                        :class="[
                            is_liked === true ? 'text-theme-lead' : 'text-theme-black/0',
                            'absolute w-fit h-fit fas fa-thumbs-up left-0 right-0 top-0 bottom-0.5 m-auto transition-colors duration-200 ease-in-out'
                        ]"
                    ></i>
                    <i class="absolute w-fit h-fit far fa-thumbs-up left-0 right-0 top-0 bottom-0.5 m-auto"></i>
                </div>
                <!--like count-->
                <div class="w-full h-full relative text-base font-medium">
                    <span class="absolute w-fit h-fit left-2 top-0 bottom-0 m-auto">
                        <span v-if="is_liked" class="sr-only">you have liked this</span>
                        <!-- <span class="sr-only">current like count is </span>{{ prettyLikeCount }} -->
                        <span class="sr-only">current like count is </span>999M
                    </span>
                </div>
            </button>
            <!--dislike-->
            <button
                ref="dislike_button"
                @click.stop="handleDisliked()"
                class="col-span-1 h-full px-4 flex flex-row bg-theme-light/60    hover:bg-theme-light/80 hover:border-theme-light-trim/40 hover:shadow-sm       border-t-2 border-theme-light-trim rounded-full rounded-l-none shadow-md transition duration-150 ease-in-out"
                type="button"
            >
                <!--dislike button-->
                <div
                    class="w-6 h-full relative"
                    ref="dislike_logo"
                >
                    <i
                        :class="[
                            is_liked === false ? 'text-theme-lead' : 'text-theme-black/0',
                            'absolute w-fit h-fit fas fa-thumbs-down left-0 right-0 top-2 bottom-0 m-auto transition-colors duration-200 ease-in-out'
                        ]"
                    ></i>
                    <i class="absolute w-fit h-fit far fa-thumbs-down left-0 right-0 top-2 bottom-0 m-auto"></i>
                </div>
                <!--dislike count-->
                <div class="w-full h-full relative text-base font-medium">
                    <span class="absolute w-fit h-fit left-2 top-0 bottom-0 m-auto">
                        <span v-if="is_liked === false" class="sr-only">you have disliked this</span>
                        <!-- <span class="sr-only">current dislike count is </span>{{ prettyDislikeCount }} -->
                        <span class="sr-only">current dislike count is </span>999K
                    </span>
                </div>
            </button>
        </div>
    </div>
</template>


<script setup lang="ts">

</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import anime from 'animejs';
    import { prettyCount } from '@/helper_functions';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                is_liked: null as boolean|null,
                like_count: 0,
                dislike_count: 0,
                submit_interval: null as number|null,
            };
        },
        props: {
            propEventId: {
                type: Number,
                required: true,
                default: null,
            },
            propLikeCount: {
                type: Number,
                required: true,
                default: 0,
            },
            propDislikeCount: {
                type: Number,
                required: true,
                default: 0,
            },
            propIsLiked: {
                type: Boolean,
                required: false,
                default: null,
            },
        },
        computed: {
            prettyLikeCount() : string {

                if(this.is_liked === true){

                    return prettyCount(this.like_count + 1);

                }else if(this.is_liked === null){

                    return prettyCount(this.like_count);
                    
                }

                return prettyCount(this.like_count);
            },
            prettyDislikeCount() : string {

                if(this.is_liked === false){

                    return prettyCount(this.dislike_count + 1);

                }else if(this.is_liked === null){

                    return prettyCount(this.dislike_count);
                }

                return prettyCount(this.dislike_count);
            },
        },
        mounted(){

            this.axiosSetup();

            //store props into variables
            this.is_liked = this.propIsLiked;
            this.like_count = this.propLikeCount;
            this.dislike_count = this.propDislikeCount;

            //we expect counts from REST API to also include user's own like/dislike
            //if user has like/dislike, we -1 first, so at computed, we can +1 for existing or new like/dislike
            if(this.propIsLiked === true){

                this.like_count -= 1;

            }else if(this.propIsLiked === false){

                this.dislike_count -= 1;
            }
        },
        methods: {
            submitLikeDislike() : void {

                if(this.propEventId === null){

                    return;
                }

                if(this.submit_interval !== null){

                    clearTimeout(this.submit_interval);
                }

                //we use this to counter spam-clicking
                this.submit_interval = window.setTimeout(()=>{

                    let data = new FormData();
                
                    data.append('event_id', JSON.stringify(this.propEventId));
                    data.append('is_liked', JSON.stringify(this.is_liked));

                    axios.post('http://127.0.0.1:8000/api/event-likes-dislikes', data)
                    .then(() => {})
                    .catch(() => {

                        //revert
                        //we want to do this with logic instead of simply using previous value
                        //because on fail, previous value is inaccurate when spam-clicked
                        if(this.is_liked === true){

                            this.handleLiked();

                        }else if(this.is_liked === false){

                            this.handleDisliked();
                        }
                    });
                }, 500);
            },
            handleLiked() : void {

                if(this.propEventId === null){

                    return;
                }

                if(this.is_liked === null || this.is_liked === false){

                    this.is_liked = true;
                    this.animeLikeDislike('like', true);

                }else{

                    this.is_liked = null;
                    this.animeLikeDislike('like', false);
                }

                this.submitLikeDislike();
            },
            handleDisliked() : void {

                if(this.propEventId === null){

                    return;
                }

                if(this.is_liked === null || this.is_liked === true){

                    this.is_liked = false;
                    this.animeLikeDislike('dislike', true);

                }else{

                    this.is_liked = null;
                    this.animeLikeDislike('dislike', false);
                }

                this.submitLikeDislike();
            },
            animeLikeDislike(like_or_dislike:'like'|'dislike', is_adding:boolean) : void {

                const like_element = this.$refs.like_logo as HTMLElement;
                const dislike_element = this.$refs.dislike_logo as HTMLElement;

                //always remove anime on new action to prevent old anime from trying to finish
                anime.remove(like_element);
                like_element.style.transform = 'scale(100%)';
                like_element.style.rotate = '0deg';

                anime.remove(dislike_element);
                dislike_element.style.transform = 'scale(100%)';
                dislike_element.style.rotate = '0deg';

                //determine target
                let target;

                if(like_or_dislike === 'like'){

                    target = like_element;

                }else if(like_or_dislike === 'dislike'){

                    target = dislike_element;

                }else{

                    console.log('Implementation error on like/dislike.');
                    return;
                }

                if(is_adding){

                    //i.e. from nothing to liked
                    anime({
                        targets: target,
                        rotate: ['-45deg', '15deg', '0deg'],
                        scale: ['150%', '100%'],
                        duration: 500,
                        autoplay: true,
                        loop: false,
                        easing: 'linear',
                    });

                }else{

                    //i.e. from liked to unliked
                    anime({
                        targets: target,
                        rotate: ['-15deg', '15deg', '0deg'],
                        duration: 500,
                        autoplay: true,
                        loop: false,
                        easing: 'linear',
                    });
                }
            },
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                let token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return false;
                }

                axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
                axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
                return true;
            },
        },
    });
</script>