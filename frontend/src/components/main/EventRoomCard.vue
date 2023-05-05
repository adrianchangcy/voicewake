<template>
    <div
        :class="[
            propIsInContainer === true ? 'border-2 border-theme-light-gray rounded-lg px-4 py-6' : '',
            'flex flex-col gap-8'
        ]"
    >

        <!--title and datetime-->
        <div
            v-if="propShowTitle === true"
            class="h-fit"
        >
            <!--title from user 1-->
            <p class="text-xl">
                {{ propEventRoom.event_room.event_room_name }}
            </p>
            <!--last updated-->
            <p class="text-base font-light">
                {{ prettyWhenCreated }}
            </p>
        </div>

        <!--originator-->
        <div
            v-if="propEventRoom.originator !== null"
        >
            <VUser
                :propUsername="propEventRoom.originator.user_event_role.user.username"
            />

            <div
                v-if="propShowOnePlaybackPerEvent === true"
                class="w-full h-fit grid grid-cols-8 gap-2"
            >
                <div class="col-span-6">
                    <VPlayback
                        :propAudioVolumePeaks="propEventRoom.originator.audio_volume_peaks"
                        :propBucketQuantity="propEventRoom.originator.audio_volume_peaks.length"
                        :propAudioURL="propEventRoom.originator.audio_file"
                    />
                </div>
                <div class="col-span-2 relative border border-theme-light-gray rounded-lg">
                    <span class="text-3xl w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">{{ propEventRoom.originator.event_tone.event_tone_symbol }}</span>
                </div>
            </div>
            <div v-else>
                <VEventCard
                    :propEvent="propEventRoom.originator"
                />
            </div>

            <div class="w-full h-fit grid grid-cols-8 pt-2">
                <VLikeDislike
                    :propEventId="propEventRoom.originator.id"
                    :propLikeCount="propEventRoom.originator.like_count"
                    :propDislikeCount="propEventRoom.originator.dislike_count"
                    :propIsLiked="propEventRoom.originator.is_liked_by_user"
                    class="col-span-6 lg:col-span-5"
                />
            </div>
        </div>

        <!--responders-->
        <div
            v-for="event in propEventRoom.responder" :key="event.id"
        >
            <VUser
                :propUsername="event.user_event_role.user.username"
            />

            <div
                v-if="propShowOnePlaybackPerEvent === true"
                class="w-full h-fit grid grid-cols-8 gap-2"
            >
                <div class="col-span-6">
                    <VPlayback
                        :propAudioVolumePeaks="event.audio_volume_peaks"
                        :propBucketQuantity="event.audio_volume_peaks.length"
                        :propAudioURL="event.audio_file"
                    />
                </div>
                <div class="col-span-2 relative border border-theme-light-gray rounded-lg">
                    <span class="text-3xl w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">{{ event.event_tone.event_tone_symbol }}</span>
                </div>
            </div>
            <div v-else>
                <VEventCard
                    :propEvent="event"
                />
            </div>
            <div class="w-full h-fit grid grid-cols-8 pt-2">
                <VLikeDislike
                    :propEventId="event.id"
                    :propLikeCount="event.like_count"
                    :propDislikeCount="event.dislike_count"
                    :propIsLiked="event.is_liked_by_user"
                    class="col-span-6 lg:col-span-5"
                />
            </div>
        </div>

        <!--reply-->
        <div v-if="propShowReplyMenu === true">
            <VCreateEvents
                :propIsOriginator="false"
                :propEventRoomId="propEventRoom.event_room.id"
            />
        </div>
        <div v-else>
            <VActionButtonBig
                :propIsSmaller="true"
                @click.stop="confirmReplyChoice()"
            >
                Reply
            </VActionButtonBig>
        </div>
    </div>
</template>

<script setup lang="ts">

    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VEventCard from '/src/components/small/VEventCard.vue';
    import VLikeDislike from '/src/components/medium/VLikeDislike.vue';
    import VUser from '/src/components/small/VUser.vue';
    import VActionButtonBig from '../small/VActionButtonBig.vue';
    import VCreateEvents from '../medium/VCreateEvents.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { timeDifferenceUTC } from '@/helper_functions';
    import EventRoomTypes from '@/types/EventRooms.interface';
    const axios = require('axios');

    export default defineComponent({
        data() {
            return {
                selected_event_id: null as number|null,
            };
        },
        props: {
            propEventRoom: {
                type: Object as PropType<EventRoomTypes>,
                required: true,
            },
            propShowTitle: {
                type: Boolean,
                default: true
            },
            propShowOnePlaybackPerEvent: {
                type: Boolean,
                default: false
            },
            propShowReplyMenu: {
                type: Boolean,
                default: false
            },
            propIsInContainer: {
                type: Boolean,
                default: false
            }
        },
        computed: {
            prettyWhenCreated(){

                return timeDifferenceUTC(new Date(this.propEventRoom.event_room.when_created));
            },
            redirectURL(){
                
                return '/hear/' + (this.propEventRoom.event_room.id).toString();
            }
        },
        methods: {
            async confirmReplyChoice(){

                console.log('yolo');
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

            //set up Axios appropriately
            this.axiosSetup();
        },
    });
</script>