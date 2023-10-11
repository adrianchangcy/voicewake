<template>
    <div>

        <div class="h-10 grid grid-cols-6 gap-1 text-xl text-theme-black">

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
                    <span class="sr-only">like button</span>
                    <span v-show="is_liked === true" class="sr-only">you have liked this</span>
                    <div class="w-fit h-full mx-auto flex flex-row">
                        <!--like logo-->
                        <div
                            class="h-full flex items-center relative pb-0.5"
                            ref="like_logo"
                        >
                            <i
                                :class="[
                                    is_liked === true ? 'text-theme-lead' : 'text-theme-black/0',
                                    'w-fit h-fit fas fa-thumbs-up mx-auto transition-colors'
                                ]"
                                aria-hidden="true"
                            ></i>
                            <i class="absolute w-fit h-fit far fa-thumbs-up mx-auto" aria-hidden="true"></i>
                        </div>
                        <!--like count-->
                        <div
                            v-show="prettyLikeCount !== ''"
                            class="w-fit h-full pl-1 lg:pl-2 flex items-center text-sm lg:text-base font-medium"
                        >
                            <span class="w-fit h-fit mx-auto">
                                {{ prettyLikeCount }}
                            </span>
                        </div>
                    </div>
                </button>

                <!--dislike-->
                <button
                    ref="dislike_button"
                    @click.stop="handleDisliked()"
                    class="col-span-1 h-full     shade-border-when-hover transition-colors      bg-theme-light       border border-l-0 border-theme-light-gray rounded-full rounded-l-none     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
                    type="button"
                >
                    <span class="sr-only">dislike button</span>
                    <span v-show="is_liked === false" class="sr-only">you have disliked this</span>
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
                                aria-hidden="true"
                            ></i>
                            <i class="absolute w-fit h-fit far fa-thumbs-down mx-auto" aria-hidden="true"></i>
                        </div>
                        <!--dislike count-->
                        <div
                            v-show="prettyDislikeCount !== ''"
                            class="w-fit h-full pl-1 lg:pl-2 flex items-center text-sm lg:text-base font-medium"
                        >
                            <span class="w-fit h-fit mx-auto">
                                {{ prettyDislikeCount }}
                            </span>
                        </div>
                    </div>
                </button>
            </div>

            <!--share-->
            <button
                @click="copyEventURL()"
                class="h-full col-span-1 relative flex flex-row items-center     shade-border-when-hover transition-colors      bg-theme-light       border border-theme-light-gray rounded-full     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
                type="button"
            >
                <TransitionGroupFade :prop-has-absolute="true">
                    <span v-show="has_shared === false" class="w-full flex items-center text-center">
                        <i class="fas fa-share text-base mx-auto" aria-hidden="true"></i>
                        <span class="sr-only">Copy recording URL to share</span>
                    </span>
                    <span v-show="has_shared === true" class="w-full flex items-center text-center">
                        <i class="fas fa-check text-base mx-auto" aria-hidden="true"></i>
                        <span class="sr-only">recording URL copied</span>
                    </span>
                </TransitionGroupFade>
            </button>

            <!--more options-->
            <button
                ref="open_close_extra_options_menu_button"
                @click="toggleExtraOptionsMenu()"
                class="h-full col-span-1 relative flex items-center     transition-colors shade-border-when-hover border-theme-light-gray      bg-theme-light       border rounded-full     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
                type="button"
            >
                <i class="fas fa-ellipsis-vertical text-base mx-auto" aria-hidden="true"></i>
                <span v-show="!is_extra_options_menu_open" class="sr-only">open extra options menu</span>
                <span v-show="is_extra_options_menu_open" class="sr-only">close extra options menu</span>
            </button>
        </div>

        <!--arrows-->
        <div class="w-full h-0 grid grid-cols-6 gap-1">
            <div class="col-start-6 col-span-1 relative">
                <div
                    v-show="is_extra_options_menu_open"
                    class="z-30 w-2 h-2 absolute top-3 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"
                ></div>
            </div>
        </div>

        <!--menu-->
        <div class="w-full h-0 relative">

            <div
                v-show="is_extra_options_menu_open"
                v-click-outside="{
                    var_name_for_element_bool_status: 'is_extra_options_menu_open',
                    refs_to_exclude: ['open_close_extra_options_menu_button']
                }"
                class="absolute w-fit h-fit right-0 m-auto p-2 top-4 z-20 flex flex-col rounded-lg border-2 border-theme-black bg-theme-light"
            >
                <VActionTextOnly
                    @click="submitReport()"
                    :prop-is-enabled="!has_reported && !is_reporting"
                    propElement="button"
                    type="button"
                    propFontSize="s"
                    propElementSize="s"
                    :prop-is-icon-only="false"
                    class="w-fit px-2"
                >

                    <span v-if="is_reporting">
                        <VLoading prop-element-size="s">
                            <span class="pl-2">Reporting...</span>
                        </VLoading>
                    </span>
                    <span v-else>
                        <i class="fas fa-flag w-fit h-fit text-sm"></i>
                        <span v-show="!has_reported" class="pl-2">Report</span>
                        <span v-show="has_reported" class="pl-2">Reported</span>
                    </span>
                </VActionTextOnly>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import VActionTextOnly from '../small/VActionTextOnly.vue';
    import VLoading from '../small/VLoading.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import anime from 'animejs';
    import { prettyCount } from '@/helper_functions';
    import { notify } from 'notiwind';
    import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';
    import { useCurrentLikesDislikesStore } from '@/stores/CurrentLikesDislikesStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                current_likes_dislikes_store: useCurrentLikesDislikesStore(),
                pop_up_manager_store: usePopUpManagerStore(),

                is_liked: null as boolean|null,
                like_count: 0,
                dislike_count: 0,
                minimum_dislike_count_for_display: 10,
                minimum_dislike_percentage_for_display: 0.2,
                submit_interval: null as number|null,

                has_shared: false,
                has_shared_timeout: null as number|null,

                is_reporting: false,
                has_reported: false,

                is_extra_options_menu_open: false,
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
            propFilteredGroupedEventsStoreEventRoomIndex: {
                type: Number,
                default: null
            },
            propFilteredGroupedEventsStoreEventIndex: {
                type: Number,
                default: null
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
            toggleExtraOptionsMenu() : void {

                this.is_extra_options_menu_open = !this.is_extra_options_menu_open;
            },
            async copyEventURL() : Promise<void> {

                if(this.has_shared_timeout !== null){

                    return;
                }

                const url = window.origin + "/event/" + this.propEventRoomId;
                navigator.clipboard.writeText(url);

                notify({
                    title: 'Link copied',
                    type: 'ok',
                }, 2000);

                this.has_shared = true;

                this.has_shared_timeout = window.setTimeout(()=>{
                    this.has_shared = false;
                    this.has_shared_timeout !== null ? window.clearTimeout(this.has_shared_timeout) : null;
                    this.has_shared_timeout = null;
                }, 2000);
            },
            async submitLikeDislike() : Promise<void> {

                this.submit_interval !== null ? clearTimeout(this.submit_interval) : null;

                //we use this to counter spam-clicking
                this.submit_interval = window.setTimeout(()=>{

                    let data = new FormData();
                
                    data.append('event_id', JSON.stringify(this.propEvent['id']));
                    data.append('is_liked', JSON.stringify(this.is_liked));

                    const is_liked_value = this.is_liked;

                    axios.post('http://127.0.0.1:8000/api/event-likes-dislikes', data)
                    .then(() => {

                        this.current_likes_dislikes_store.addLikeDislike(this.propEvent.id, is_liked_value);
                    })
                    .catch((error:any) => {

                        //revert
                        this.is_liked = this.propEvent['is_liked_by_user'];

                        notify({
                            title: "Error",
                            text: JSON.parse(error.request.response)['message'],
                            type: "error"
                        }, 3000);
                    });
                }, 500);
            },
            async isLoggedIn() : Promise<boolean> {

                if(this.pop_up_manager_store.getIsLoggedIn === false){

                    this.pop_up_manager_store.toggleIsLoginRequiredPromptOpen(true);
                    return false;
                }

                return true;
            },
            async handleLiked() : Promise<void> {

                if(await this.isLoggedIn() === false){

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
            async handleDisliked() : Promise<void> {

                if(await this.isLoggedIn() === false){

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
            async submitReport() : Promise<void> {

                if(await this.isLoggedIn() === false){

                    return;
                }

                this.is_reporting = true;

                let data = new FormData();
                
                data.append('reported_event_id', JSON.stringify(this.propEvent['id']));

                axios.post('http://127.0.0.1:8000/api/event-reports/create', data)
                .then(() => {

                    this.has_reported = true;

                    notify({
                        icon: 'fas fa-flag',
                        title: 'Recording reported',
                        text: 'Thank you for bringing this to our attention. We will review it shortly.',
                        type: 'generic',
                    }, 6000);

                }).catch(() => {

                    notify({
                        icon: 'fas fa-check',
                        title: 'Report failed',
                        text: 'Oops! Unable to report this recording.',
                        type: 'error',
                    }, 2000);

                }).finally(() => {

                    this.is_reporting = false;
                });
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
        },
        beforeMount(){

            //accurately deduct user's own is_liked from count
            this.like_count = this.propEvent.like_count - (this.propEvent.is_liked_by_user === true ? 1 : 0);
            this.dislike_count = this.propEvent.dislike_count - (this.propEvent.is_liked_by_user === false ? 1 : 0);

            //check if store has latest is_liked, and is different from API results' is_liked
            //we use the store because it is always updated, while API results are not updated when user changes is_liked
            const likes_dislikes_store = this.current_likes_dislikes_store.getCurrentLikesDislikes;

            if(
                this.propEvent.id in likes_dislikes_store === true &&
                this.propEvent.is_liked_by_user !== likes_dislikes_store[this.propEvent.id]
            )

                this.is_liked = likes_dislikes_store[this.propEvent.id];

            else{

                this.is_liked = this.propEvent.is_liked_by_user;
            }
        },
    });
</script>