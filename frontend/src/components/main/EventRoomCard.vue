<template>
    <div
        class="flex flex-col gap-8"
    >

        <!--title and datetime-->
        <div
            v-if="propShowTitle === true"
            class="h-fit"
        >
            <!--title from user 1-->
            <p class="text-xl break-words">
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
            class="flex flex-col gap-2"
        >
            <VUser
                :propUsername="propEventRoom.originator.user_event_role.user.username"
            />

            <div
                v-if="propShowOnePlaybackPerEvent === true"
                class="w-full h-fit"
            >
                <VPlayback
                    :propAudioVolumePeaks="propEventRoom.originator.audio_volume_peaks"
                    :propBucketQuantity="propEventRoom.originator.audio_volume_peaks.length"
                    :propAudioURL="propEventRoom.originator.audio_file"
                    :propEventToneSymbol="propEventRoom.originator.event_tone.event_tone_symbol"
                />
            </div>
            <div v-else>
                <VEventCard
                    :propEvent="propEventRoom.originator"
                />
            </div>

            <div class="w-full h-fit grid grid-cols-8">
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
            class="flex flex-col gap-2"
        >
            <VUser
                :propUsername="event.user_event_role.user.username"
            />

            <div
                v-if="propShowOnePlaybackPerEvent === true"
                class="w-full h-fit"
            >
                <VPlayback
                    :propAudioVolumePeaks="event.audio_volume_peaks"
                    :propBucketQuantity="event.audio_volume_peaks.length"
                    :propAudioURL="event.audio_file"
                    :propEventToneSymbol="event.event_tone.event_tone_symbol"
                />
            </div>
            <div v-else>
                <VEventCard
                    :propEvent="event"
                />
            </div>
            <div class="w-full h-fit grid grid-cols-8">
                <VLikeDislike
                    :propEventId="event.id"
                    :propLikeCount="event.like_count"
                    :propDislikeCount="event.dislike_count"
                    :propIsLiked="event.is_liked_by_user"
                    class="col-span-6 lg:col-span-5"
                />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VEventCard from '/src/components/small/VEventCard.vue';
    import VLikeDislike from '/src/components/medium/VLikeDislike.vue';
    import VUser from '/src/components/small/VUser.vue';
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
        },
        computed: {
            prettyWhenCreated(){

                return timeDifferenceUTC(new Date(this.propEventRoom.event_room.when_created));
            },
        },
        methods: {
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