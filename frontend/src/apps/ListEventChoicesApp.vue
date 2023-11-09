<template>
    <div class="text-theme-black">

        <!--title-->
        <!--logo only here, since "Reply" goes away for certain parts, and putting it here would make things jolt-->
        <!--you can find "Reply" at areas that need it instead-->
        <!--for "Reply", we use pb-10 instead of pb-8 here due to the font overflowing out at current size-->
        <VTitle
            propFontSize="l"
            class="pt-8"
        >
            <template #title>
                <div class="flex flex-col text-center">
                    <i class="fas fa-comments text-2xl" aria-hidden="true"></i>
                </div>
            </template>
        </VTitle>

        <!--content-->
        <div class="relative">

            <TransitionGroupFade
                :propHasAbsolute="true"
            >

                <!--search and any dialog-->
                <div
                    v-show="(canSearch || hasUnfinishedReply) && !canChooseReplyChoices"
                    class="w-full h-fit"
                >

                    <VTitle
                        propFontSize="l"
                        class="pb-10"
                    >
                        <template #title>
                            <div class="flex flex-col">
                                <span class="block w-full text-center">
                                    Reply
                                </span>
                            </div>
                        </template>
                    </VTitle>

                    <!--content-->
                    <TransitionGroupFade
                        :propHasAbsolute="true"
                    >

                        <!--can search-->
                        <div
                            v-show="canSearch"
                            class="w-full h-fit"
                        >
                            <!--search-->
                            <VActionSpecial
                                @click.stop="getEvents()"
                                :propIsEnabled="canSearch"
                                propElement="button"
                                type="button"
                                propElementSize="2xl"
                                propFontSize="2xl"
                                :propIsRound="true"
                                class="w-40 block mx-auto"
                            >
                                <span class="block mx-auto">
                                    Search
                                </span>
                            </VActionSpecial>

                            <!--dialog-->
                            <!--we must pre-write them because the variables are reset before transition, causing warp-->
                            <div class="mt-10 relative">

                                <TransitionGroupFade
                                    :propHasAbsolute="true"
                                >

                                    <!--no new audio-clips-->
                                    <VDialogPlain
                                        v-show="current_simple_dialog === simple_dialogs[0]"
                                        :prop-has-border="false"
                                        :prop-has-auto-spacing="false"
                                        class="w-full"
                                    >
                                        <template #logo>
                                            <i class="far fa-face-meh-blank" aria-hidden="true"></i>
                                        </template>
                                        <template #title>
                                            <span>No new recordings found.</span>
                                        </template>
                                        <template #content>
                                            <span>Search again in a moment!</span>
                                        </template>
                                    </VDialogPlain>

                                    <!--reply choice expired-->
                                    <VDialogPlain
                                        v-show="current_simple_dialog === simple_dialogs[1]"
                                        :prop-has-border="false"
                                        :prop-has-auto-spacing="false"
                                        class="w-full"
                                    >
                                        <template #logo>
                                            <i class="fas fa-hourglass-end" aria-hidden="true"></i>
                                        </template>
                                        <template #title>
                                            <span>Reply choice has expired.</span>
                                        </template>
                                        <template #content>
                                            <span>Search again for more!</span>
                                        </template>
                                    </VDialogPlain>
                                </TransitionGroupFade>
                            </div>
                        </div>

                        <!--is_replying dialog-->
                        <div
                            v-show="hasUnfinishedReply"
                            class="w-full h-fit"
                        >

                            <!--dialog to complete or delete unfinished reply before continuing-->
                            <VDialogPlain
                                class="w-full h-fit"
                            >
                                <template #title>
                                    <span class="block">1 unfinished reply found.</span>
                                </template>
                                <template #content>
                                    <span class="block text-center">
                                        Open and complete your reply, or delete it, before searching.
                                    </span>
                                    <div
                                        class="grid grid-rows-1 grid-cols-2 pt-4 gap-2"
                                    >
                                        <VActionSpecial
                                            propElement="a"
                                            :href="redirect_url"
                                            propElementSize="s"
                                            propFontSize="s"
                                            class="col-span-1"
                                        >
                                            <span class="block mx-auto">Open</span>
                                        </VActionSpecial>
                                        <VAction
                                            @click.stop="deleteUnfinishedReply()"
                                            :propIsEnabled="!is_unfinished_reply_deleting"
                                            propElement="button"
                                            type="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            class="col-span-1"
                                        >
                                            <span class="block mx-auto">Delete</span>
                                        </VAction>
                                    </div>
                                </template>
                            </VDialogPlain>
                        </div>
                    </TransitionGroupFade>
                </div>

                <!--all loading-related stuff-->
                <div
                    v-show="isLoading"
                    class="w-full h-fit"
                >

                    <TransitionGroupFade
                        :propHasAbsolute="true"
                    >

                        <!--searching-->
                        <div
                            v-show="is_searching"
                            class="w-full h-fit"
                        >
                            <!--reply/skip skeleton-->
                            <div class="w-full h-fit grid grid-cols-2 gap-4 pb-8">
                                <div class="col-span-1 justify-self-end">
                                    <div class="w-24 h-24 rounded-full skeleton"></div>
                                </div>
                                <div class="col-span-1">
                                    <div class="w-24 h-24 rounded-full skeleton"></div>
                                </div>
                            </div>
                            <!--audio_clip room skeleton-->
                            <EventCardSkeleton
                                :prop-has-border="true"
                                :prop-audio-clip-quantity="1"
                            />
                        </div>

                        <!--deleting unfinished reply-->
                        <div
                            v-show="is_unfinished_reply_deleting"
                            class="w-full h-fit"
                        >

                            <VTitle
                                propFontSize="l"
                                class="pb-10"
                            >
                                <template #title>
                                    <div class="flex flex-col">
                                        <span class="block w-full text-center">
                                            Reply
                                        </span>
                                    </div>
                                </template>
                            </VTitle>

                            <div class="w-full h-40 flex items-center text-xl font-medium">
                                <div class="w-full flex flex-col">
                                    <i class="fas fa-eraser block mx-auto animate-pulse" aria-hidden="true"></i>
                                    <span class="block mx-auto">Deleting unfinished reply...</span>
                                </div>
                            </div>
                        </div>

                        <!--confirming new reply choice-->
                        <div
                            v-show="is_new_reply_choice_confirming"
                            class="w-full h-fit"
                        >

                            <VTitle
                                propFontSize="l"
                                class="pb-10"
                            >
                                <template #title>
                                    <div class="flex flex-col">
                                        <span class="block w-full text-center">
                                            Reply
                                        </span>
                                    </div>
                                </template>
                            </VTitle>

                            <div class="w-full h-40 flex items-center text-xl font-medium">
                                <div class="w-full flex flex-col">
                                    <VLoading
                                        propElementSize="m"
                                        class="mx-auto"
                                    />
                                    <span class="mx-auto">Confirming reply choice...</span>
                                </div>
                            </div>
                        </div>

                        <!--expiring new reply choice-->
                        <div
                            v-show="is_expiry_loading"
                            class="w-full h-fit"
                        >

                            <VTitle
                                propFontSize="l"
                                class="pb-10"
                            >
                                <template #title>
                                    <div class="flex flex-col">
                                        <span class="block w-full text-center">
                                            Reply
                                        </span>
                                    </div>
                                </template>
                            </VTitle>

                            <div class="w-full h-40 flex items-center text-xl font-medium">
                                <div class="w-full flex flex-col">
                                    <VLoading
                                        propElementSize="m"
                                        class="mx-auto"
                                    />
                                    <span class="mx-auto">Loading...</span>
                                </div>
                            </div>
                        </div>

                    </TransitionGroupFade>
                </div>

                <!--can show reply choices-->
                <div
                    v-show="canChooseReplyChoices"
                    class="w-full h-fit"
                >

                    <div class="w-full h-fit pb-8 grid grid-cols-2 gap-4">

                        <!--reply-->
                        <div class="col-span-1 justify-self-end">
                            <VActionSpecial
                                @click.stop="confirmReplyChoice(getMainEvent)"
                                :propIsEnabled="!is_new_reply_choice_confirming"
                                propElement="button"
                                type="button"
                                propElementSize="l"
                                propFontSize="m"
                                :propIsRound="true"
                                class="w-24"
                            >
                                <span class="block mx-auto">Reply</span>
                            </VActionSpecial>
                        </div>

                        <!--skip-->
                        <div class="col-span-1">
                            <VAction
                                @click.stop="getEvents()"
                                :propIsEnabled="canSearch"
                                propElement="button"
                                type="button"
                                propElementSize="l"
                                propFontSize="m"
                                :propIsRound="true"
                                class="w-24"
                            >
                                <span class="block mx-auto">Skip</span>
                            </VAction>
                        </div>
                    </div>

                    <!--event preview-->
                    <!--must use v-if since EventCard cannot exist with null-->
                    <TransitionFade>
                        <EventCard
                            v-if="canChooseReplyChoices"
                            :propEvent="getMainEvent"
                            :propShowTitle="true"
                            :propHasBorder="true"
                        />
                    </TransitionFade>
                </div>
            </TransitionGroupFade>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VTitle from '/src/components/small/VTitle.vue';
    import EventCard from '/src/components/main/EventCard.vue';
    import EventCardSkeleton from '@/components/skeleton/EventCardSkeleton.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VAction from '@/components/small/VAction.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VDialogPlain from '/src/components/small/VDialogPlain.vue';
    import VLoading from '/src/components/small/VLoading.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeFromNowMS, prettyTimeRemaining } from '@/helper_functions';
    import { notify } from 'notiwind';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    import StatusValues from '@/types/values/StatusValues';
    import { useUnfinishedReplyStore } from '@/stores/UnfinishedReplyStore';
    import AudioClipTonesTypes from '@/types/AudioClipTones.interface';

    const axios = require('axios');

    export default defineComponent({
        name: "ListEventChoicesApp",
        data() {
            return {
                unfinished_reply_store: useUnfinishedReplyStore(),

                new_reply_choice_events: [] as EventsAndAudioClipsTypes[] | [],
                unfinished_reply_event: null as EventsAndAudioClipsTypes | null,
                redirect_url: "",

                is_sort_menu_open: false,
                selected_audio_clip_tone: null as AudioClipTonesTypes|null,

                expiry_interval: null as number | null,
                expiry_string: "",
                new_reply_choice_expiry_max_ms: 0,   //will be replaced with SSR data on beforeMount()
                unfinished_reply_expiry_max_ms: 0,   //will be replaced with SSR data on beforeMount()
                expiry_interval_checkpoint_ms: 80000, //when to switch from slowest_expiry_interval_ms to fastest_expiry_interval_ms
                slowest_expiry_interval_ms: 10000,
                fastest_expiry_interval_ms: 1000,

                is_searching: false,
                is_unfinished_reply_deleting: false,
                is_expiry_loading: false,
                is_new_reply_choice_confirming: false,

                simple_dialogs: ["no_reply_choices", "choosing_audio_clip_choice_expired", "reply_deleted"] as StatusValues[],
                current_simple_dialog: "",
            };
        },
        computed: {
            getMainEvent() : EventsAndAudioClipsTypes|null {

                //only useful for current 1-event-per-instance
                //use v-for when > 1 in the future

                if(this.new_reply_choice_events.length === 0){

                    return null;

                }else{

                    return this.new_reply_choice_events[0];
                }
            },
            isLoading() : boolean {
                return this.is_searching === true || this.is_unfinished_reply_deleting === true ||
                    this.is_expiry_loading === true || this.is_new_reply_choice_confirming === true;
            },
            hasUnfinishedReply() : boolean {

                return this.unfinished_reply_event !== null && this.isLoading === false;
            },
            canChooseReplyChoices() : boolean {

                return this.new_reply_choice_events.length > 0 && this.hasUnfinishedReply === false &&
                    this.isLoading === false;
            },
            canSearch() : boolean {

                return this.unfinished_reply_event === null && this.isLoading === false;
            },
        },
        methods: {
            async handleNewSelectedAudioClipTone(new_value:AudioClipTonesTypes|null) : Promise<void> {

                this.selected_audio_clip_tone = new_value;

                this.getEvents();
            },
            toggleSortMenu() : void {

                this.is_sort_menu_open = !this.is_sort_menu_open;
            },
            handleUnfinishedReplyStoreChange() : void {

                const store_status = this.unfinished_reply_store.getStatus;
                const extra_allowed_store_status:StatusValues[] = [
                    "replying", "replying_deleted", "replying_expired", "replying_successful"
                ];

                //store_status must be "", or
                if(
                    this.simple_dialogs.includes(store_status) === false &&
                    extra_allowed_store_status.includes(store_status) === false
                ){

                    return;
                }

                switch(store_status){

                    case 'choosing_audio_clip_choice_expired':

                        this.current_simple_dialog = store_status;
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.new_reply_choice_events = [];
                        this.unfinished_reply_event = null;
                        break;

                    case 'replying_deleted':

                        this.current_simple_dialog = store_status;
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.new_reply_choice_events = [];
                        this.unfinished_reply_event = null;
                        break;

                    case 'replying_expired':

                        this.current_simple_dialog = "";
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.new_reply_choice_events = [];
                        this.unfinished_reply_event = null;
                        break;

                    case 'replying':

                        this.current_simple_dialog = "";
                        this.new_reply_choice_events = [];
                        break;

                    case 'replying_successful':

                        this.current_simple_dialog = "";
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.new_reply_choice_events = [];
                        this.unfinished_reply_event = null;
                        break;

                    default:

                        break;
                }
            },
            async doExpire(context:"unfinished_reply"|"new_reply_choices"): Promise<void> {

                if(this.is_expiry_loading === true){

                    return;
                }

                this.is_expiry_loading = true;

                let data = new FormData();
                const specific_url = context === "unfinished_reply" ? "reply/cancel" : "reply/delete";

                if(context === "unfinished_reply" && this.unfinished_reply_event !== null){

                    data.append("event_id", JSON.stringify(this.unfinished_reply_event.event.id));
                }


                await axios.post(window.location.origin + "/api/events/" + specific_url, data)
                .then(() => {

                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";
                    this.current_simple_dialog = this.simple_dialogs[1];
                    this.new_reply_choice_events = [];
                    this.is_expiry_loading = false;

                    //patch store
                    if(context === "unfinished_reply"){

                        this.unfinished_reply_store.$patch({
                            status: "replying_expired"
                        });
                    
                    }else{

                        this.unfinished_reply_store.$patch({
                            event: null,
                            status: "choosing_audio_clip_choice_expired"
                        });
                    }
                })
                .catch(() => {

                    //whether expiring fails or not,
                    //it is better to reset as usual to prevent any further confusing actions
                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";
                    this.current_simple_dialog = this.simple_dialogs[1];
                    this.new_reply_choice_events = [];
                    this.is_expiry_loading = false;

                    //patch store
                    if(context === "unfinished_reply"){

                        this.unfinished_reply_store.$patch({
                            status: "replying_expired"
                        });
                    
                    }else{

                        this.unfinished_reply_store.$patch({
                            event: null,
                            status: "choosing_audio_clip_choice_expired"
                        });
                    }
                });
            },
            //you can call this for new reply choices, the API will remove previous reply choices for us
            async getEvents(): Promise<void> {

                if(this.canSearch === false){

                    return;
                }

                //reset
                this.current_simple_dialog = "";
                this.new_reply_choice_events = [];
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                this.is_searching = true;

                let data = new FormData();

                if(this.selected_audio_clip_tone !== null){

                    data.append('audio_clip_tone_id', JSON.stringify(this.selected_audio_clip_tone.id));
                }

                await axios.post(window.location.origin + "/api/events/reply/choices/list", data)
                .then((result:any) => {

                    if(result.data["data"].length === 0){

                        //no audio_clips
                        this.current_simple_dialog = this.simple_dialogs[0];

                        //reset
                        //patch store
                        this.unfinished_reply_store.$patch({
                            event: null,
                            status: "no_reply_choices"
                        });

                    }else if(result.data["data"].length > 0 && result.data["data"][0]["event"]["is_replying"] === true){

                        //user has unfinished reply
                        this.unfinished_reply_event = result.data["data"][0];
                        this.redirect_url = "hear/" + this.unfinished_reply_event!.event.id.toString();
                        this.startExpiryInterval("unfinished_reply");

                        //patch store
                        this.unfinished_reply_store.$patch({
                            event: result.data["data"][0],
                            status: "replying"
                        });

                    }else{

                        //user has new reply choices
                        this.new_reply_choice_events = result.data["data"];
                        this.startExpiryInterval("new_reply_choices");

                        //patch store
                        this.unfinished_reply_store.$patch({
                            event: null,
                            status: "choosing_audio_clip_choice"
                        });
                    }

                })
                .catch((error:any) => {

                    let error_text = '';

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        title: "Event search failed",
                        text: error_text,
                        type: "error"
                    }, 3000);

                }).finally(()=>{

                    this.is_searching = false;
                });
            },
            async deleteUnfinishedReply(): Promise<void> {

                if(this.unfinished_reply_event === null || this.is_unfinished_reply_deleting === true){
                    return;
                }

                this.is_unfinished_reply_deleting = true;
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                const handler = ()=>{

                    this.is_unfinished_reply_deleting = false;
                    this.unfinished_reply_event = null;

                    //patch store
                    this.unfinished_reply_store.$patch({
                        status: "replying_deleted"
                    });
                };

                //cancel previous reply choice
                let data = new FormData();
                data.append("event_id", JSON.stringify(this.unfinished_reply_event.event.id));

                await axios.post(window.location.origin + "/api/events/reply/delete", data)
                .then(() => {

                    //auto-search
                    this.getEvents();
                })
                .catch((error:any) => {

                    let error_text = '';

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        //401 is when you cannot cancel because you are no longer replying
                        //happens when cronjob cancels first
                        if(error.request.status === 401){

                            return;
                        }

                        error_text = error.response.data['message'];
                    }

                    notify({
                        title: 'Reply deletion failed',
                        text: error_text,
                        type: 'error'
                    }, 4000);

                }).then(()=>{

                    handler();
                });
            },
            async confirmReplyChoice(event: EventsAndAudioClipsTypes|null): Promise<void> {

                if (event === null || this.is_new_reply_choice_confirming === true){

                    return;
                }
                
                this.is_new_reply_choice_confirming = true;
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                let data = new FormData();
                data.append("event_id", JSON.stringify(event.event.id));

                await axios.post(window.location.origin + "/api/events/reply/start", data)
                .then((result:any) => {

                    if(result.request.status === 202){

                        //store unfinished reply
                        //we have no backend<-->store relation to trigger reset when server deems it expired
                        //so we just override the store when user confirms reply choice, only possible without unfinished reply
                        //patch store
                        this.unfinished_reply_store.$patch({
                            event: this.getMainEvent,
                            status: "replying"
                        });

                        //redirect
                        window.location.href = window.location.origin + "/event/" + event.event.id.toString();

                    }else{

                        this.is_new_reply_choice_confirming = false;

                        notify({
                            title: "Reply selection failed",
                            text: "Unable to select for reply. " + result.data['message'],
                            type: "error"
                        }, 3000);
                    }

                })
                .catch((error:any) => {

                    this.is_new_reply_choice_confirming = false;

                    let error_text = '';

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        error_text = error.response.data['message'];

                        if(error.request.status === 404){

                            //either no longer exists or unavailable
                            //auto-skip
                            this.getEvents();

                        }else{

                            //restart expiry interval
                            this.startExpiryInterval("new_reply_choices");
                        }
                    }

                    notify({
                        title: "Reply selection failed",
                        text: error_text,
                        type: "error"
                    }, 3000);
                });
            },
            startExpiryInterval(context:"new_reply_choices"|"unfinished_reply"): void {

                let target_event: EventsAndAudioClipsTypes | null = null;
                let target_max_ms = 0;

                if(
                    context === "unfinished_reply" &&
                    this.unfinished_reply_event !== null
                ){

                    target_event = this.unfinished_reply_event;
                    target_max_ms = this.unfinished_reply_expiry_max_ms;

                }else if(context === "new_reply_choices" && this.new_reply_choice_events.length > 0){

                    target_event = this.new_reply_choice_events[0];
                    target_max_ms = this.new_reply_choice_expiry_max_ms;

                }else{

                    return;
                }

                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_interval = null;

                if(target_event.event.when_locked === null){

                    return;
                }

                const when_locked_ms = new Date(target_event.event.when_locked!);
                const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                //time is up
                if (time_elapsed_ms >= target_max_ms) {

                    this.unfinished_reply_event === null ? this.doExpire(context) : this.deleteUnfinishedReply();
                    return;
                }

                //proceed

                //run every 1s if <120s remaining, else run every 60s
                //change this again once sped up
                let interval_ms:number = (
                    (target_max_ms - time_elapsed_ms) <= this.expiry_interval_checkpoint_ms ?
                    this.fastest_expiry_interval_ms : this.slowest_expiry_interval_ms
                );

                //set possible first time expiry string
                const time_remaining = prettyTimeRemaining(time_elapsed_ms, target_max_ms);
                this.expiry_string = time_remaining === "" ? "" : time_remaining as string;

                //declare this here for reusability
                const interval_function = () => {

                    //get time difference
                    const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                    //time is up
                    if (time_elapsed_ms >= target_max_ms) {

                        this.unfinished_reply_event === null ? this.doExpire(context) : this.deleteUnfinishedReply();
                    }

                    //if interval started with >1000, reinitialise itself for new interval with shorter time
                    if (
                        interval_ms === this.slowest_expiry_interval_ms &&
                        (target_max_ms - time_elapsed_ms) <= this.expiry_interval_checkpoint_ms
                    ){

                        clearInterval(this.expiry_interval!);

                        this.expiry_interval = window.setInterval(interval_function, this.fastest_expiry_interval_ms);

                        //change interval_ms as a lazy way to ensure this 'if' block runs once only
                        interval_ms = this.fastest_expiry_interval_ms;
                    }

                    //set string
                    const time_remaining = prettyTimeRemaining(time_elapsed_ms, target_max_ms);
                    this.expiry_string = time_remaining === "" ? "" : time_remaining as string;
                };

                //start interval
                this.expiry_interval = window.setInterval(interval_function, interval_ms);
            },
        },
        beforeMount(){

            const container = (document.getElementById('data-container-list-event-choices') as HTMLElement);

            //get essential data first, where we don't proceed if they don't exist
            const audio_clip_choice_expiry_seconds = (container.getAttribute('data-event-reply-choice-expiry-seconds') as string);
            const audio_clip_reply_expiry_seconds = (container.getAttribute('data-event-reply-expiry-seconds') as string);

            if(audio_clip_choice_expiry_seconds === null || audio_clip_reply_expiry_seconds === null){

                //don't proceed because we lack essential data
                console.log('Essential data was not passed into template.');
                return;
            }

            //get data from SSR template
            this.new_reply_choice_expiry_max_ms = parseInt(audio_clip_choice_expiry_seconds) * 1000;
            this.unfinished_reply_expiry_max_ms = parseInt(audio_clip_reply_expiry_seconds) * 1000;

            //handle unfinished reply being cancelled/expired from elsewhere
            this.unfinished_reply_store.$subscribe(()=>{

                this.handleUnfinishedReplyStoreChange();
            });
        },
    });
</script>