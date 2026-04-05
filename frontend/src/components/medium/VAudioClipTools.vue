<template>
    <div class="">

        <!--put ref here to target closest vue virtual scroller-->
        <div
            ref="v_audio_clip_tools_main"
            class="h-10 grid grid-cols-6 gap-1 text-xl"
        >

            <!--like/dislike-->
            <div class="h-full col-span-4 grid grid-cols-2 relative parent-trigger-shade-fake-border-when-hover">

                <!--fake border-->
                <div class="absolute w-[1px] h-[50%] left-0 right-0 top-0 bottom-0 m-auto bg-theme-gray-2 dark:bg-dark-theme-gray-2 shade-fake-border-when-hover transition-colors">
                </div>

                <!--like-->
                <button
                    @click="handleLikeDislike(true)"
                    class="col-span-1 h-full     shade-border-when-hover transition-colors      bg-transparent       border border-r-0 border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-full rounded-r-none active:bg-theme-gray-3 dark:active:bg-dark-theme-gray-3    focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline dark:focus-visible:outline-dark-theme-outline"
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
                            <FontAwesomeIcon
                                icon="fas fa-thumbs-up"
                                :class="[
                                    is_liked === true ? 'text-theme-lead dark:text-dark-theme-lead' : 'text-theme-lead/0',
                                    'mx-auto transition-colors'
                                ]"
                            />
                            <FontAwesomeIcon
                                icon="far fa-thumbs-up"
                                :class="[
                                    is_liked === true ? 'text-theme-black dark:text-dark-theme-lead' : '',
                                    'absolute mx-auto transition-colors'
                                ]"
                            />
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
                    @click="handleLikeDislike(false)"
                    class="col-span-1 h-full     shade-border-when-hover transition-colors      bg-transparent       border border-l-0 border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-full rounded-l-none active:bg-theme-gray-3 dark:active:bg-dark-theme-gray-3     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline dark:focus-visible:outline-dark-theme-outline"
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
                            <FontAwesomeIcon
                                icon="fas fa-thumbs-down"
                                :class="[
                                    is_liked === false ? 'text-theme-lead dark:text-dark-theme-lead' : 'text-theme-lead/0',
                                    'mx-auto transition-colors'
                                ]"
                            />
                            <FontAwesomeIcon
                                icon="far fa-thumbs-down"
                                :class="[
                                    is_liked === false ? 'text-theme-black dark:text-dark-theme-lead' : '',
                                    'absolute mx-auto transition-colors'
                                ]"
                            />
                        </div>
                        <!--dislike count-->
                        <div
                            v-show="canShowDislikeCount"
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
                class="h-full col-span-1 flex items-center     shade-border-when-hover transition-colors      bg-transparent       border border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-full active:bg-theme-gray-3 dark:active:bg-dark-theme-gray-3     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline dark:focus-visible:outline-dark-theme-outline"
                type="button"
            >
                <TransitionGroupFade>
                    <span v-show="has_shared === false" class="w-full h-full flex items-center text-center">
                        <FontAwesomeIcon icon="fas fa-share" class="text-base mx-auto"/>
                        <span class="sr-only">Copy recording URL to share</span>
                    </span>
                    <span v-show="has_shared === true" class="w-full h-full flex items-center text-center">
                        <FontAwesomeIcon icon="fas fa-check" class="text-base mx-auto"/>
                        <span class="sr-only">recording URL copied</span>
                    </span>
                </TransitionGroupFade>
            </button>

            <!--more options-->
            <button
                ref="open_close_extra_options_menu_button"
                @click="toggleExtraOptionsMenu()"
                :class="[
                    is_extra_options_menu_open ? 'border-2 border-theme-black dark:border-dark-theme-white-2' : 'border border-theme-gray-2 dark:border-dark-theme-gray-2 shade-border-when-hover',
                    'h-full col-span-1 relative flex items-center   active:bg-theme-gray-3 dark:active:bg-dark-theme-gray-3     transition-colors       bg-transparent       rounded-full     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline'
                ]"
                type="button"
            >
                <FontAwesomeIcon icon="fas fa-ellipsis-vertical" class="text-base mx-auto"/>
                <span v-show="!is_extra_options_menu_open" class="sr-only">open extra options menu</span>
                <span v-show="is_extra_options_menu_open" class="sr-only">close extra options menu</span>
            </button>
        </div>

        <!--arrow and menu-->
        <div
            v-if="is_extra_options_menu_open"
            class="w-full h-0 relative"
        >

            <!--menu-->
            <div
                v-click-outside="{
                    bool_status_variable_or_callback: forceCloseExtraOptionsMenu,
                    refs_to_exclude: ['open_close_extra_options_menu_button']
                }"
                class="absolute top-3 w-28 h-fit right-0 m-auto p-2 flex flex-col rounded-lg border-2 border-theme-black dark:border-dark-theme-white-2 bg-theme-light dark:bg-theme-dark"
            >

                <VActionText
                    v-if="propIsSuperuser || is_own_audio_clip"
                    @click="emitNewAudioClipAction('delete')"
                    :prop-is-enabled="isAnyExtraOptionProcessing"
                    propElement="button"
                    type="button"
                    propFontSize="s"
                    propElementSize="s"
                    
                    class="w-full"
                >

                    <span class="w-fit">
                        <VLoading
                            v-if="is_deleting"
                            prop-element-size="s"
                        />
                        <div v-else class="flex items-center">
                            <FontAwesomeIcon icon="fas fa-trash" class="text-sm px-2 pb-0.5"/>
                            <span>Delete</span>
                        </div>
                    </span>
                </VActionText>

                <VActionText
                    v-if="propIsSuperuser"
                    @click="emitNewAudioClipAction('ban')"
                    :prop-is-enabled="isAnyExtraOptionProcessing"
                    propElement="button"
                    type="button"
                    propFontSize="s"
                    propElementSize="s"
                    
                    class="w-full"
                >

                    <span class="w-fit">
                        <VLoading
                            v-if="is_banning"
                            prop-element-size="s"
                        />
                        <div v-else class="flex items-center">
                            <FontAwesomeIcon icon="fas fa-flag" class="text-sm px-2"/>
                            <span>Ban</span>
                        </div>
                    </span>
                </VActionText>

                <VActionText
                    v-if="!is_own_audio_clip"
                    @click="emitNewAudioClipAction('report')"
                    :prop-is-enabled="isAnyExtraOptionProcessing"
                    propElement="button"
                    type="button"
                    propFontSize="s"
                    propElementSize="s"
                    
                    class="w-full"
                >

                    <span class="w-fit">
                        <VLoading
                            v-if="is_reporting"
                            prop-element-size="s"
                        />
                        <div v-else class="flex items-center">
                            <FontAwesomeIcon icon="fas fa-flag" class="text-sm px-2"/>
                            <span>Report</span>
                        </div>
                    </span>
                </VActionText>
            </div>

            <!--arrow-->
            <div class="grid grid-cols-6 gap-1">
                <div class="col-start-6 col-span-1 relative">
                    <div
                        class="w-2 h-2 absolute top-2 left-0 right-0 mx-auto bg-theme-light dark:bg-theme-dark border-l-2 border-t-2 border-theme-black dark:border-dark-theme-white-2 rotate-45"
                    ></div>
                </div>
            </div>

        </div>
    </div>
</template>


<script setup lang="ts">
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import VActionText from '@/components/small/VActionText.vue';
    import VLoading from '@/components/small/VLoading.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faThumbsUp as farThumbsUp } from '@fortawesome/free-regular-svg-icons/faThumbsUp';
    import { faThumbsUp as fasThumbsUp } from '@fortawesome/free-solid-svg-icons/faThumbsUp';
    import { faThumbsDown as farThumbsDown } from '@fortawesome/free-regular-svg-icons/faThumbsDown';
    import { faThumbsDown as fasThumbsDown } from '@fortawesome/free-solid-svg-icons/faThumbsDown';
    import { faShare } from '@fortawesome/free-solid-svg-icons/faShare';
    import { faCheck } from '@fortawesome/free-solid-svg-icons/faCheck';
    import { faEllipsisVertical } from '@fortawesome/free-solid-svg-icons/faEllipsisVertical';
    import { faFlag } from '@fortawesome/free-solid-svg-icons/faFlag';
    import { faTrash } from '@fortawesome/free-solid-svg-icons/faTrash';

    library.add(farThumbsUp, fasThumbsUp, farThumbsDown, fasThumbsDown, faShare, faCheck, faEllipsisVertical, faFlag, faTrash);
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { animate, utils } from 'animejs';
    import { prettyCount } from '@/helper_functions';
    import { notify } from '@/wrappers/notify_wrapper';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    import axios from 'axios';

    import AudioClipActionsTypes from '@/types/AudioClipActions.interface';

    export default defineComponent({
        data(){
            return {
                pop_up_manager_store: usePopUpManagerStore(),

                is_own_audio_clip: false,

                is_liked: null as boolean|null,
                previous_is_liked: null as boolean|null,
                like_count: 0,
                dislike_count: 0,
                minimum_dislike_count_for_display: 10,
                minimum_dislike_percentage_for_display: 0.2,
                submit_timeout: null as number|null,

                has_shared: false,
                has_shared_timeout: null as number|null,

                is_deleting: false,
                is_banning: false,
                is_reporting: false,

                is_extra_options_menu_open: false,
            };
        },
        props: {
            propAudioClip: {
                type: Object as PropType<AudioClipsAndLikeDetailsTypes>,
                required: true,
            },
            propHasVirtualScroll: {
                type: Boolean,
                default: false,
            },
            propCallablePopupLoginRequired: {
                type: Function,
                required: true,
            },
            propIsLoggedIn: {
                type: Boolean,
                required: true,
            },
            propIsSuperuser: {
                type: Boolean,
                required: true,
            },
            propUsername: {
                type: String,
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
            isAnyExtraOptionProcessing() : boolean {

                return (
                    this.is_deleting === false &&
                    this.is_banning === false &&
                    this.is_reporting === false
                );
            }
        },
        watch: {
            propAudioClip(){

                //this is used for virtual scroll

                this.syncLikesDislikes();
                this.toggleExtraOptionsMenu(false);
                this.submit_timeout= null;
                this.has_shared = false;
                this.has_shared_timeout = null;
                this.is_deleting = false;
                this.is_banning = false;
                this.is_reporting = false;
            },
        },
        emits: [
            'newIsLiked',
            'newAudioClipAction',
        ],
        methods: {
            forceCloseExtraOptionsMenu() : void {

                this.toggleExtraOptionsMenu(false);
            },
            emitNewIsLiked(audio_clip:AudioClipsAndLikeDetailsTypes, new_is_liked:boolean|null) : void {

                this.$emit('newIsLiked', {
                    'audio_clip': audio_clip,
                    'new_is_liked': new_is_liked,
                });
            },
            emitNewAudioClipAction(action:'delete'|'ban'|'report') : void {

                if(this.isAnyExtraOptionProcessing === false){

                    return;
                }

                let api_request:()=>Promise<void>;

                if(action === 'delete'){

                    api_request = this.submitDelete;

                }else if(action === 'ban'){

                    api_request = this.submitBan;

                }else if(action === 'report'){

                    api_request = this.submitReport;

                }else{

                    throw new Error('Unrecognised action.');
                }

                let audio_clip = {} as AudioClipsAndLikeDetailsTypes;
                Object.assign(audio_clip, this.propAudioClip);

                this.$emit('newAudioClipAction', {
                    'audio_clip': audio_clip,
                    'action': action,
                    'api_request': api_request,
                    'event_list_index': null,   //filled by VEventCard if necessary
                } as AudioClipActionsTypes);
            },
            toggleExtraOptionsMenu(force_is_open:boolean|null=null) : void {

                const final_state = force_is_open === null ? !this.is_extra_options_menu_open : force_is_open;

                if(this.propHasVirtualScroll === true){

                    const closest_virtual_scroll_view = (this.$refs.v_audio_clip_tools_main as HTMLElement).closest('.vue-recycle-scroller__item-view');

                    (closest_virtual_scroll_view as HTMLElement).style.zIndex = final_state === true ? '1' : '';
                }

                this.is_extra_options_menu_open = final_state;
            },
            async copyAudioClipURL() : Promise<void> {

                if(this.has_shared_timeout !== null){

                    return;
                }

                const url = window.location.origin + "/event/" + this.propAudioClip.event_id;

                //this will raise error in insecure context, i.e. not HTTPS
                navigator.clipboard.writeText(url);

                notify({
                    type: 'ok',
                    title: 'Link copied',
                    text: '',
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

                //do Object.assign in case prop changes while API is still running
                let audio_clip = {} as AudioClipsAndLikeDetailsTypes;
                Object.assign(audio_clip, this.propAudioClip);

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
                            type: 'error',
                            title: 'Action failed',
                            text: error_text,
                        }, 3000);
                    });
                }, 500);
            },
            checkIsLoggedIn() : boolean {

                if(this.propIsLoggedIn === false){

                    this.propCallablePopupLoginRequired();
                    return false;
                }

                return true;
            },
            async handleLikeDislike(is_liked_action:boolean) : Promise<void> {

                if(this.checkIsLoggedIn() === false){

                    //already shown dialog
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
            animeLikeDislike(is_liked:boolean, is_adding:boolean) : void {

                const like_element = this.$refs.like_logo as HTMLElement;
                const dislike_element = this.$refs.dislike_logo as HTMLElement;

                //always remove anime on new action to prevent old anime from trying to finish
                utils.remove(like_element);
                like_element.style.transform = 'scale(100%)';
                like_element.style.rotate = '0deg';

                utils.remove(dislike_element);
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
                    animate(target, {
                        rotate: ['-45deg', '15deg', '0deg'],
                        scale: ['150%', '100%'],
                        duration: 500,
                        autoplay: true,
                        loop: false,
                        ease: 'linear',
                    });

                }else{

                    //i.e. from liked to unliked
                    animate(target, {
                        rotate: ['-15deg', '15deg', '0deg'],
                        duration: 500,
                        autoplay: true,
                        loop: false,
                        ease: 'linear',
                    });
                }
            },
            syncLikesDislikes() : void {

                this.like_count = this.propAudioClip.like_count;
                this.dislike_count = this.propAudioClip.dislike_count;
                this.is_liked = this.propAudioClip.is_liked_by_user;

                if(Object.hasOwn(this.propAudioClip, 'previous_is_liked_by_user') === true){

                    this.previous_is_liked = this.propAudioClip.previous_is_liked_by_user!;
                }
            },
            async submitDelete() : Promise<void> {

                this.is_deleting = true;

                let audio_clip = {} as AudioClipsAndLikeDetailsTypes;
                Object.assign(audio_clip, this.propAudioClip);

                return axios.delete(`${window.location.origin}/api/audio-clips/delete/${audio_clip.id}`)
                .then((result:any) => {

                    if(result.request.status !== 204){

                        throw new Error(`result.request.status of ${result.request.status} is not recognised.`);
                    }

                    notify({
                        type: 'ok',
                        title: 'Recording deleted',
                        text: 'The incomplete event has been removed from the front page.',
                    }, 3000);

                }).catch((error:any) => {

                    let error_text = 'Oops! Something went wrong.';

                    if(
                        Object.hasOwn(error, 'request') === true &&
                        Object.hasOwn(error, 'response') === true &&
                        Object.hasOwn(error.response, 'data') === true &&
                        Object.hasOwn(error.response.data, 'message') === true &&
                        error.response.data['message'].length > 0
                    ){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        type: 'error',
                        title: 'Deletion failed',
                        text: error_text,
                    }, 3000);

                }).finally(() => {

                    this.is_deleting = false;
                });
            },
            async submitBan() : Promise<void> {

                this.is_banning = true;

                let audio_clip = {} as AudioClipsAndLikeDetailsTypes;
                Object.assign(audio_clip, this.propAudioClip);

                let data = new FormData();

                data.append('audio_clip_id', JSON.stringify(audio_clip.id));

                return axios.post(window.location.origin + '/api/audio-clips/bans', data)
                .then((result:any) => {

                    if(result.request.status !== 200){

                        throw new Error(`result.request.status of ${result.request.status} is not recognised.`);
                    }

                    notify({
                        type: 'ok',
                        title: 'Recording banned',
                        text: 'The recording and its owner has been banned.',
                    }, 3000);

                }).catch((error:any) => {

                    let error_text = 'Oops! Something went wrong.';

                    if(
                        Object.hasOwn(error, 'request') === true &&
                        Object.hasOwn(error, 'response') === true &&
                        Object.hasOwn(error.response, 'data') === true &&
                        Object.hasOwn(error.response.data, 'message') === true &&
                        error.response.data['message'].length > 0
                    ){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        type: 'error',
                        title: 'Ban failed',
                        text: error_text,
                    }, 3000);

                    throw error;

                }).finally(() => {

                    this.is_banning = false;
                });
            },
            async submitReport() : Promise<void> {

                this.is_reporting = true;

                let audio_clip = {} as AudioClipsAndLikeDetailsTypes;
                Object.assign(audio_clip, this.propAudioClip);

                let data = new FormData();
                
                data.append('audio_clip_id', JSON.stringify(audio_clip.id));

                return axios.post(window.location.origin + '/api/audio-clips/reports', data)
                .then(() => {

                    notify({
                        type: 'generic',
                        title: 'Recording reported',
                        text: 'We will evaluate this recording soon.',
                        icon: {'font_awesome': 'fas fa-flag'},
                    }, 3000);

                }).catch((error:any) => {

                    let error_text = 'Oops! Unable to report this recording.';

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        type: 'error',
                        title: 'Report failed',
                        text: error_text,
                    }, 3000);

                }).finally(() => {

                    this.is_reporting = false;
                });
            },
        },
        beforeMount(){

            this.syncLikesDislikes();

            this.is_own_audio_clip = this.propUsername === this.propAudioClip.user.username;
        },
    });
</script>