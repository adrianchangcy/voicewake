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
                    @click="handleLikeDislike(true)"
                    class="col-span-1 h-full     shade-border-when-hover active:bg-theme-lightest-gray transition-colors      bg-theme-light       border border-r-0 border-theme-light-gray rounded-full rounded-r-none    focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
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
                    @click="handleLikeDislike(false)"
                    class="col-span-1 h-full     shade-border-when-hover active:bg-theme-lightest-gray transition-colors      bg-theme-light       border border-l-0 border-theme-light-gray rounded-full rounded-l-none     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
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
                @click="copyAudioClipURL()"
                class="h-full col-span-1 relative flex flex-row items-center     shade-border-when-hover active:bg-theme-lightest-gray transition-colors      bg-theme-light       border border-theme-light-gray rounded-full     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
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
                class="h-full col-span-1 relative flex items-center     transition-colors shade-border-when-hover active:bg-theme-lightest-gray border-theme-light-gray      bg-theme-light       border rounded-full     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
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
                    :prop-is-enabled="!is_reporting"
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
                        <span class="pl-2">Report</span>
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
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                pop_up_manager_store: usePopUpManagerStore(),

                is_liked: null as boolean|null,
                previous_is_liked: null as boolean|null,
                like_count: 0,
                dislike_count: 0,
                minimum_dislike_count_for_display: 10,
                minimum_dislike_percentage_for_display: 0.2,
                submit_timeout: null as number|null,

                has_shared: false,
                has_shared_timeout: null as number|null,

                is_reporting: false,

                is_extra_options_menu_open: false,
            };
        },
        props: {
            propAudioClip: {
                type: Object as PropType<AudioClipsAndLikeDetailsTypes>,
                required: true,
            },
            propEventId: {
                type: Number,
                required: true,
            },
        },
        computed: {
            prettyLikeCount() : string {
                
                if(this.like_count === 0){

                    return '';
                }

                return prettyCount(this.like_count);
            },
            prettyDislikeCount() : string {

                if(this.dislike_count === 0){

                    return '';
                }

                return prettyCount(this.dislike_count);
            },
            canShowDislikeCount() : boolean {

                const is_percentage_ok = (
                    (
                        this.dislike_count /
                        (this.like_count + this.dislike_count)
                    ) > this.minimum_dislike_percentage_for_display
                );

                const is_count_ok = this.dislike_count >= this.minimum_dislike_count_for_display;

                return (is_percentage_ok === true && is_count_ok === true);
            },
        },
        watch: {
            propAudioClip(){

                this.syncLikesDislikes();
            },
        },
        emits: [
            'newIsLiked',
        ],
        methods: {
            toggleExtraOptionsMenu() : void {

                this.is_extra_options_menu_open = !this.is_extra_options_menu_open;
            },
            async copyAudioClipURL() : Promise<void> {

                if(this.has_shared_timeout !== null){

                    return;
                }

                const url = window.location.origin + "/event/" + this.propEventId;
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

                this.submit_timeout !== null ? clearTimeout(this.submit_timeout) : null;

                const audio_clip = this.propAudioClip;
                const is_liked = this.is_liked;

                //we use this to counter spam-clicking
                this.submit_timeout = window.setTimeout(async ()=>{

                    let data = new FormData();
                
                    data.append('audio_clip_id', JSON.stringify(audio_clip.id));
                    data.append('is_liked', JSON.stringify(is_liked));

                    axios.post(window.location.origin + '/api/audio-clips/likes-dislikes', data)
                    .then(() => {

                        //update store
                        this.emitNewIsLiked(audio_clip, is_liked);

                    }).catch(async (error:any)=>{

                        //revert
                        //store acts as a source of truth, until user closes tab before request completes
                        //nonetheless, server has the ultimate truth

                        if(audio_clip === this.propAudioClip){

                            this.is_liked = audio_clip.is_liked_by_user;
                            this.like_count = audio_clip.like_count;
                            this.dislike_count = audio_clip.dislike_count;
                        }

                        let error_text = 'Oops! Something went wrong.';

                        if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                            error_text = error.response.data['message'];
                        }

                        notify({
                            icon: 'fas fa-check',
                            title: 'Action failed',
                            text: error_text,
                            type: 'error',
                        }, 3000);
                    });
                }, 500);
            },
            async isLoggedIn() : Promise<boolean> {

                if(this.pop_up_manager_store.isLoggedIn === false){

                    this.pop_up_manager_store.toggleIsLoginRequiredPromptOpen(true);
                    return false;
                }

                return true;
            },
            async handleLikeDislike(is_liked_action:boolean) : Promise<void> {

                if(await this.isLoggedIn() === false){

                    return;
                }

                let is_liked:boolean|null = is_liked_action;

                if(is_liked_action === this.is_liked){

                    is_liked = null;
                }

                switch(is_liked){

                    case true:

                        if(this.is_liked === false){

                            this.dislike_count -= 1;
                        }

                        if(this.is_liked !== true){

                            this.like_count += 1;
                        }

                        break;

                    case null:

                        switch(this.is_liked){
                            case true:
                                this.like_count -= 1;
                                break;
                            case false:
                                this.dislike_count -= 1;
                                break;
                            default:
                                break;
                        }

                        break;
                    
                    case false:
                    
                        if(this.is_liked === true){
                        
                            this.like_count -= 1;
                        }
                    
                        if(this.is_liked !== false){
                        
                            this.dislike_count += 1;
                        }
                    
                        break;
                    
                    default:
                    
                        break;
                }

                //do anime
                this.animeLikeDislike(is_liked_action, (is_liked !== null));

                //save
                this.previous_is_liked = this.is_liked;
                this.is_liked = is_liked;

                //submit
                this.submitLikeDislike();
            },
            async submitReport() : Promise<void> {

                if(await this.isLoggedIn() === false){

                    return;
                }

                this.is_reporting = true;

                let data = new FormData();
                
                data.append('reported_audio_clip_id', JSON.stringify(this.propAudioClip['id']));

                axios.post(window.location.origin + '/api/audio-clips/reports', data)
                .then(() => {

                    notify({
                        icon: 'fas fa-flag',
                        title: 'Recording reported',
                        text: 'Thank you for bringing this to our attention.',
                        type: 'generic',
                    }, 3000);

                }).catch((error:any) => {

                    let error_text = 'Oops! Unable to report this recording.';

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        icon: 'fas fa-check',
                        title: 'Report failed',
                        text: error_text,
                        type: 'error',
                    }, 3000);

                }).finally(() => {

                    this.is_reporting = false;
                });
            },
            animeLikeDislike(is_liked:boolean, is_adding:boolean) : void {

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

                if(is_liked === true){

                    target = like_element;

                }else if(is_liked === false){

                    target = dislike_element;
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
            async syncLikesDislikes() : Promise<void> {

                this.like_count = this.propAudioClip.like_count;
                this.dislike_count = this.propAudioClip.dislike_count;
                this.is_liked = this.propAudioClip.is_liked_by_user;

                if(Object.hasOwn(this.propAudioClip, 'previous_is_liked_by_user') === true){

                    this.previous_is_liked = this.propAudioClip.previous_is_liked_by_user!;
                }
            },
            async emitNewIsLiked(audio_clip:AudioClipsAndLikeDetailsTypes, new_is_liked:boolean|null) : Promise<void> {

                this.$emit('newIsLiked', {
                    'audio_clip': audio_clip,
                    'new_is_liked': new_is_liked,
                });
            },
        },
        beforeMount(){

            this.syncLikesDislikes();
        },
    });
</script>