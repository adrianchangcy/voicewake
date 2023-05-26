<template>
    <div
        class="flex flex-col gap-8"
    >

        <!--title and datetime-->
        <div
            v-if="propShowTitle === true"
            class="h-fit"
        >
            <!--title-->
            <p class="text-xl break-words">
                {{ propEventRoom.event_room.event_room_name }}
            </p>
            <!--when created-->
            <p class="text-base font-light">
                {{ pretty_when_created }}
            </p>
        </div>

        <!--originator-->
        <div
            v-if="propEventRoom.originator !== null"
            class="flex flex-col gap-2"
        >
            <VUser
                :propUsername="propEventRoom.originator.user.username"
            />

            <div
                v-if="hasMultipleEvents === false"
                class="h-fit"
            >
                    <VPlayback
                        :propAudioVolumePeaks="propEventRoom.originator.audio_volume_peaks"
                        :propBucketQuantity="propEventRoom.originator.audio_volume_peaks.length"
                        :propAudioURL="propEventRoom.originator.audio_file"
                        :propEventTone="propEventRoom.originator.event_tone"
                    />
            </div>
            <div v-else>
                <VEventCard
                    :propEvent="propEventRoom.originator"
                    @isSelected="handleNewSelectedEvent($event)"
                    :propIsSelected="checkIsSelected(propEventRoom.originator.id)"
                />
            </div>

            <div class="w-full h-fit grid grid-cols-8">
                <VLikeDislike
                    :propEventId="propEventRoom.originator.id"
                    :propLikeCount="propEventRoom.originator.like_count"
                    :propDislikeCount="propEventRoom.originator.dislike_count"
                    :propIsLiked="propEventRoom.originator.is_liked_by_user"
                    class="col-span-6 lg:col-span-4"
                />
            </div>
        </div>

        <!--responders-->
        <div v-if="hasMultipleEvents === false">
            <div
                v-for="event in propEventRoom.responder" :key="event.id"
                class="flex flex-col gap-2"
            >
                <VUser
                    :propUsername="event.user.username"
                />
                <div class="w-full h-fit">
                    <VPlayback
                        :propAudioVolumePeaks="event.audio_volume_peaks"
                        :propBucketQuantity="event.audio_volume_peaks.length"
                        :propAudioURL="event.audio_file"
                        :propEventTone="event.event_tone"
                    />
                </div>
                <div class="w-full h-fit grid grid-cols-8">
                    <VLikeDislike
                        :propEventId="event.id"
                        :propLikeCount="event.like_count"
                        :propDislikeCount="event.dislike_count"
                        :propIsLiked="event.is_liked_by_user"
                        class="col-span-6 lg:col-span-4"
                    />
                </div>
            </div>
        </div>
        <div v-else>
            <div
                v-for="event in propEventRoom.responder" :key="event.id"
                class="flex flex-col gap-2"
            >
                <VUser
                    :propUsername="event.user.username"
                />
                <div>
                    <VEventCard
                        :propEvent="event"
                        @isSelected="handleNewSelectedEvent($event)"
                        :propIsSelected="checkIsSelected(event.id)"
                    />
                </div>
                <div class="w-full h-fit grid grid-cols-8">
                    <VLikeDislike
                        :propEventId="event.id"
                        :propLikeCount="event.like_count"
                        :propDislikeCount="event.dislike_count"
                        :propIsLiked="event.is_liked_by_user"
                        class="col-span-6 lg:col-span-4"
                    />
                </div>
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
    import { prettyTimePassed } from '@/helper_functions';
    import EventRoomTypes from '@/types/EventRooms.interface';
    import EventTypes from '@/types/Events.interface';
    const axios = require('axios');

    export default defineComponent({
        data() {
            return {
                selected_event: null as EventTypes|null,
                pretty_when_created: '',
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
        },
        computed: {
            hasMultipleEvents() : boolean {
                return this.propEventRoom !== null &&
                    (this.propEventRoom.originator !== null && this.propEventRoom.responder.length >= 1) ||
                    (this.propEventRoom.originator === null && this.propEventRoom.responder.length >= 2);
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
            checkIsSelected(event_id:number) : boolean {

                return this.selected_event !== null && this.selected_event.id === event_id;
            },
            handleNewSelectedEvent(event:EventTypes) : void {

                this.selected_event = event;

                //since a page can have many EventRoomCard, VPlayback is placed as child to this component's parent
                //to only have one VPlayback instance across the entire page, we emit from here
                this.$emit('newSelectedEvent', event);
            }
        },
        mounted(){

            //set up Axios appropriately
            this.axiosSetup();

            this.pretty_when_created = prettyTimePassed(new Date(this.propEventRoom.event_room.when_created));
        },
        beforeUnmount(){
            
            this.$emit('newSelectedEvent', null);
        },
    });
</script>