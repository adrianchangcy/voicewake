<template>
    <div class="h-10 grid grid-cols-6 gap-0.5 sm:gap-1 text-xl text-theme-black">

        <!--like/dislike-->
        <div class="h-full col-span-4 grid grid-cols-2 relative parent-trigger-shade-fake-border-when-hover">

            <!--fake border-->
            <div class="absolute w-[1px] h-[50%] left-0 right-0 top-0 bottom-0 m-auto bg-theme-light-gray shade-fake-border-when-hover transition-colors">
            </div>

            <!--like-->
            <button
                ref="like_button"
                @click.stop="handleLiked()"
                class="col-span-1 h-full     shade-border-when-hover transition-colors      bg-theme-light       border border-r-0 border-theme-light-gray rounded-full rounded-r-none    focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
                type="button"
            >
                <div class="w-fit h-full mx-auto flex flex-row">
                    <!--like logo-->
                    <div
                        class="h-full flex items-center relative pb-1"
                        ref="like_logo"
                    >
                        <i
                            :class="[
                                is_liked === true ? 'text-theme-lead' : 'text-theme-black/0',
                                'w-fit h-fit fas fa-thumbs-up mx-auto transition-colors'
                            ]"
                        ></i>
                        <i class="absolute w-fit h-fit far fa-thumbs-up mx-auto"></i>
                    </div>
                    <!--like count-->
                    <div
                        v-show="prettyLikeCount !== ''"
                        class="w-fit h-full pl-1 lg:pl-2 flex items-center text-sm font-medium"
                    >
                        <span class="w-fit h-fit mx-auto">
                            <span class="sr-only">current like count is </span>
                            {{ prettyLikeCount }}
                        </span>
                    </div>
                    <span class="sr-only">like button</span>
                    <span v-show="is_liked === true" class="sr-only">you have liked this</span>
                </div>
            </button>

            <!--dislike-->
            <button
                ref="dislike_button"
                @click.stop="handleDisliked()"
                class="col-span-1 h-full     shade-border-when-hover transition-colors      bg-theme-light       border border-l-0 border-theme-light-gray rounded-full rounded-l-none     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
                type="button"
            >
                <div class="w-fit h-full mx-auto flex flex-row">
                    <!--dislike logo-->
                    <div
                        class="h-full flex items-center relative pt-1"
                        ref="dislike_logo"
                    >
                        <i
                            :class="[
                                is_liked === false ? 'text-theme-lead' : 'text-theme-black/0',
                                'w-fit h-fit fas fa-thumbs-down mx-auto transition-colors'
                            ]"
                        ></i>
                        <i class="absolute w-fit h-fit far fa-thumbs-down mx-auto"></i>
                    </div>
                    <!--dislike count-->
                    <div
                        v-show="prettyDislikeCount !== ''"
                        class="w-fit h-full pl-1 lg:pl-2 flex items-center text-sm font-medium"
                    >
                        <span class="w-fit h-fit mx-auto">
                            <span class="sr-only">current dislike count is </span>
                            {{ prettyDislikeCount }}
                        </span>
                    </div>
                    <span class="sr-only">dislike button</span>
                    <span v-show="is_liked === false" class="sr-only">you have disliked this</span>
                </div>
            </button>
        </div>

        <!--share-->
        <button
            @click.stop="copyEventURL()"
            class="h-full col-span-1 relative flex flex-row items-center     shade-border-when-hover transition-colors      bg-theme-light       border border-theme-light-gray rounded-full     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
            type="button"
        >
            <TransitionFade>
                <span v-if="has_shared === false" class="w-fit h-full flex items-center mx-auto">
                    <i class="fas fa-share text-base"></i>
                    <span class="sr-only">Copy URL to share</span>
                </span>
                <span v-else-if="has_shared === true" class="w-fit h-full flex items-center mx-auto">
                    <i class="fas fa-check text-base"></i>
                    <span class="hidden sm:inline pl-1 lg:pl-2 text-sm font-medium">Copied</span>
                </span>
            </TransitionFade>
        </button>

        <!--report-->
        <button
            class="h-full col-span-1 relative flex flex-row items-center     shade-border-when-hover transition-colors      bg-theme-light       border border-theme-light-gray rounded-full     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
            type="button"
        >
            <TransitionFade>
                <span v-if="has_shared === false" class="w-fit h-full flex items-center mx-auto">
                    <i class="fas fa-ellipsis-vertical text-base"></i>
                    <span class="sr-only">Copy URL to share</span>
                </span>
                <span v-else-if="has_shared === true" class="w-fit h-full flex items-center mx-auto">
                    <i class="fas fa-check text-base"></i>
                    <span class="hidden sm:inline pl-1 lg:pl-2 text-sm font-medium">Copied</span>
                </span>
            </TransitionFade>
        </button>
    </div>
</template>


<script setup lang="ts">
    import TransitionFade from '@/transitions/TransitionFade.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import anime from 'animejs';
    import { prettyCount } from '@/helper_functions';
    import { notify } from 'notiwind';
    import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                is_liked: null as boolean|null,
                like_count: 0,
                dislike_count: 0,
                minimum_dislike_count_for_display: 10,
                minimum_dislike_percentage_for_display: 0.2,
                submit_interval: null as number|null,

                has_shared: false as boolean|null,
                has_shared_timeout: null as number|null,
            };
        },
        props: {
            propEvent: {
                type: Object as PropType<EventsAndLikeDetailsTypes>,
                required: true,
            },
            propEventRoomId: {
                type: Number,
                required: true,
            },
        },
        computed: {
            prettyLikeCount() : string {
                
                if(this.is_liked === true){

                    return prettyCount(this.like_count + 1);

                }else{

                    if(this.like_count > 0){

                        return prettyCount(this.like_count);
                    }

                    return "";
                }
            },
            prettyDislikeCount() : string {

                if(this.is_liked === false){

                    const final_dislike_count = this.dislike_count + 1;

                    //only show dislikes if it passes percentage
                    if(
                        final_dislike_count >= this.minimum_dislike_count_for_display &&
                        (final_dislike_count / (this.like_count + final_dislike_count) > this.minimum_dislike_percentage_for_display)
                    ){

                        return prettyCount(final_dislike_count);
                    }

                    return "";

                }else{

                    //only show dislikes if it passes percentage
                    if(
                        this.dislike_count >= this.minimum_dislike_count_for_display &&
                        this.dislike_count / (this.like_count + this.dislike_count) > this.minimum_dislike_percentage_for_display
                    ){

                        return prettyCount(this.dislike_count);
                    }

                    return "";
                }
            },
        },
        methods: {
            copyEventURL() : void {

                const url = window.origin + "/hear/" + this.propEventRoomId;
                navigator.clipboard.writeText(url);

                this.has_shared_timeout !== null ? window.clearTimeout(this.has_shared_timeout) : null;
                this.has_shared_timeout = null;

                //code below is more complex so that it can handle "user copied but kept spamming" aesthetics

                if(this.has_shared === true){

                    this.has_shared = null;

                    this.has_shared_timeout = window.setTimeout(()=>{

                        this.has_shared = true;

                        this.has_shared_timeout !== null ? window.clearTimeout(this.has_shared_timeout) : null;
                        this.has_shared_timeout = null;

                        this.has_shared_timeout = window.setTimeout(()=>{
                            this.has_shared = false;
                        }, 2000);

                    }, 200);

                }else{

                    this.has_shared = true;

                    this.has_shared_timeout = window.setTimeout(()=>{
                        this.has_shared = false;
                    }, 2000);
                }
            },
            async submitLikeDislike() : Promise<void> {

                if(this.submit_interval !== null){

                    clearTimeout(this.submit_interval);
                }

                //we use this to counter spam-clicking
                this.submit_interval = window.setTimeout(()=>{

                    let data = new FormData();
                
                    data.append('event_id', JSON.stringify(this.propEvent['id']));
                    data.append('is_liked', JSON.stringify(this.is_liked));

                    axios.post('http://127.0.0.1:8000/api/event-likes-dislikes', data)
                    .then(() => {})
                    .catch(() => {

                        //revert
                        this.is_liked = this.propEvent['is_liked_by_user'];

                        notify({
                            title: "Error",
                            text: "Could not like or dislike this event.",
                            type: "error"
                        }, 3000);
                    });
                }, 500);
            },
            handleLiked() : void {

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
        mounted(){

            this.axiosSetup();

            //store props into variables
            this.is_liked = this.propEvent['is_liked_by_user'];
            this.like_count = this.propEvent['like_count'];
            this.dislike_count = this.propEvent['dislike_count'];

            //we expect counts from REST API to also include user's own like/dislike
            //if user has like/dislike, we -1 first, so at computed, we can +1 for existing or new like/dislike
            if(this.propEvent['is_liked_by_user'] === true){

                this.like_count -= 1;

            }else if(this.propEvent['is_liked_by_user'] === false){

                this.dislike_count -= 1;
            }
        },
    });
</script>