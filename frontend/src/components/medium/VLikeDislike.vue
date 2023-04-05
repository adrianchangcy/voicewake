<template>
    <div class="h-10 flex flex-row text-xl">
        <!--like-->
        <button
            ref="like_button"
            @click.stop="handleLiked()"
            class="w-fit h-full px-2 flex flex-row rounded-lg shade-when-hover transition-colors duration-200 ease-in-out"
            type="button"
        >
            <!--like button-->
            <div
                class="w-6 h-full relative text-xl"
                ref="like_logo"
            >
                <i
                    :class="[
                        is_liked === true ? 'text-theme-black' : 'text-theme-black/0',
                        'absolute w-fit h-fit fas fa-thumbs-up left-0 right-0 top-0 bottom-0 m-auto transition-colors duration-200 ease-in-out'
                    ]"
                ></i>
                <i class="absolute w-fit h-fit far fa-thumbs-up left-0 right-0 top-0 bottom-0 m-auto"></i>
            </div>
            <!--like count-->
            <div class="w-10 h-full relative text-base font-medium">
                <span class="absolute w-fit h-fit left-1 top-0 bottom-0 m-auto">
                    {{ prettyLikeCount }}
                </span>
            </div>
        </button>
        <!--dislike-->
        <button
            ref="dislike_button"
            @click.stop="handleDisliked()"
            class="w-fit h-full px-2 flex flex-row rounded-lg shade-when-hover transition-colors duration-200 ease-in-out"
            type="button"
        >
            <!--dislike button-->
            <div
                class="w-6 h-full relative"
                ref="dislike_logo"
            >
                <i
                    :class="[
                        is_liked === false ? 'text-theme-black' : 'text-theme-black/0',
                        'absolute w-fit h-fit fas fa-thumbs-down -scale-x-100 left-0 right-0 top-1 bottom-0 m-auto transition-colors duration-200 ease-in-out'
                    ]"
                ></i>
                <i class="absolute w-fit h-fit far fa-thumbs-down -scale-x-100 left-0 right-0 top-1 bottom-0 m-auto"></i>
            </div>
            <!--dislike count-->
            <div class="w-10 h-full relative text-base font-medium">
                <span class="absolute w-fit h-fit left-1 top-0 bottom-0 m-auto">
                    {{ prettyDislikeCount }}
                </span>
            </div>
        </button>
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
            submitLikeDislike(old_is_liked:null|boolean) : void {

                if(this.propEventId === null){

                    return;
                }

                if(this.submit_interval !== null){

                    clearTimeout(this.submit_interval);
                }

                //we use this to counter spammed clicking
                this.submit_interval = window.setTimeout(()=>{

                    let data = new FormData();
                
                    data.append('event_id', JSON.stringify(this.propEventId));

                    if(this.is_liked === null){

                        //delete
                        axios.post('http://127.0.0.1:8000/api/event-likes-dislikes', data)
                        .then(() => {})
                        .catch(() => {
                            //revert
                            this.is_liked = old_is_liked;
                        });

                    }else{

                        //create
                        data.append('is_liked', JSON.stringify(this.is_liked));

                        axios.put('http://127.0.0.1:8000/api/event-likes-dislikes', data)
                        .then(() => {})
                        .catch(() => {
                            //revert
                            this.is_liked = old_is_liked;
                        });
                    }
                }, 500);
            },
            handleLiked() : void {

                if(this.propEventId === null){

                    return;
                }

                //we want current is_liked before next change so that we can revert when needed
                const old_is_liked = this.is_liked;

                if(this.is_liked === null || this.is_liked === false){

                    this.is_liked = true;
                    this.animeLikeDislike('like', true);

                }else{

                    this.is_liked = null;
                    this.animeLikeDislike('like', false);
                }

                this.submitLikeDislike(old_is_liked);
            },
            handleDisliked() : void {

                if(this.propEventId === null){

                    return;
                }

                //we want current is_liked before next change so that we can revert when needed
                const old_is_liked = this.is_liked;

                if(this.is_liked === null || this.is_liked === true){

                    this.is_liked = false;
                    this.animeLikeDislike('dislike', true);

                }else{

                    this.is_liked = null;
                    this.animeLikeDislike('dislike', false);
                }

                this.submitLikeDislike(old_is_liked);
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