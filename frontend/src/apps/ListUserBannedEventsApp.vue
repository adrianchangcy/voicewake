<template>
    <div>

        <div class="h-10 flex items-center border-b-2 border-theme-black text-base font-medium">
            <span class="mx-auto">
                Banned recordings
            </span>
        </div>

        <EventsCard
            :prop-events="events"
            :prop-is-fetching="is_fetching"
            class="pt-14"
        />

        <div id="load-more-user-banned-events-observer-target"></div>

        <!--VEventCard emits selection, which triggers :to, thus teleporting-->
        <!--presence of VEventCard depends on VEventRoomCard-->
        <div v-if="selected_event !== null">
            <Teleport :to="playback_teleport_event_id">
                <VPlayback
                    :propEvent="selected_event"
                    :propIsOpen="true"
                    :propAudioVolumePeaks="selected_event.audio_volume_peaks"
                    :propBucketQuantity="selected_event.audio_volume_peaks.length"
                    :propAutoPlayOnSourceChange="true"
                />
            </Teleport>
        </div>
    </div>
</template>


<script setup lang="ts">
    import EventsCard from '@/components/main/EventsCard.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { prettyTimeRemaining } from '@/helper_functions';
    import EventsTypes from '@/types/Events.interface';
    import { useCurrentlyPlayingEventStore } from '@/stores/CurrentlyPlayingEventStore';
    import { notify } from 'notiwind';
    const axios = require('axios');

    export default defineComponent({
        name: 'ListUserBannedEventsApp',
        data(){
            return {
                events: [] as EventsTypes[],
                currently_playing_event_store: useCurrentlyPlayingEventStore(),
                selected_event: null as EventsTypes|null,
                playback_teleport_event_id: '',

                is_fetching: false,
                can_observer_fetch: false,
                has_no_events_left_to_fetch: false,
                current_page: 1,
            };
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
            async GetUserBannedEvents() : Promise<void> {

                this.is_fetching = true;
                this.can_observer_fetch = false;
                this.has_no_events_left_to_fetch = false;

                await axios.get(window.location.origin + '/api/users/banned-events/get/' + this.current_page.toString())
                .then((result:any) => {

                    console.log(result.data['data'].length);

                    result.data['data'].forEach((event:EventsTypes)=>{

                        this.events.push(event);
                    });

                    if(result.data['data'].length > 0){

                        this.current_page += 1;

                    }else{

                        this.has_no_events_left_to_fetch = true;

                    }

                    this.can_observer_fetch = true;

                }).catch(() => {

                    notify({
                        title: 'Error',
                        text: 'Unable to retrieve your banned recordings.',
                        type: 'error'
                    });

                }).finally(() => {

                    this.is_fetching = false;
                });
            },
            handleNewSelectedEvent(event:EventsTypes|null) : void {

                this.selected_event = event;

                if(event === null){

                    return;
                }

                //must be the same as in VEventCard
                this.playback_teleport_event_id = '#playback-teleport-event-id-' + event.id.toString();
            },
            setUpObserver() : void {

                //set up observer for infinite scroll
                const observer_target = document.querySelector('#load-more-user-banned-events-observer-target');

                const observer = new IntersectionObserver(()=>{

                    if(
                        this.can_observer_fetch === false ||
                        this.has_no_events_left_to_fetch === true
                    ){

                        return;
                    }

                    this.GetUserBannedEvents();
                }, {
                    threshold: 1,
                });

                if(observer_target !== null){

                    observer.observe(observer_target);
                }
            },
        },
        beforeMount(){

            //set up Axios appropriately
            this.axiosSetup();

            this.GetUserBannedEvents();

            //listen to store
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                this.handleNewSelectedEvent(state.playing_event as EventsTypes|null);
            });

            //make ban duration pretty
            const container = (document.getElementById('data-container-user-banned-events') as HTMLElement);

            //change '1 Jan 2023' to '1 century left'
            //we are passing 'YYYY-MM-DD HH:mm:ss' from template
            //for best reliability, Date() expects 'YYYY-MM-DDTHH:mm:ssZ'
            if(container.getElementsByClassName('banned-until').length === 1){

                const banned_until_element = container.getElementsByClassName('banned-until')[0];
                const banned_until = (container.getAttribute('data-banned-until') as string).replace(/ /g, 'T') + 'Z';
                banned_until_element.textContent = 'for ' + prettyTimeRemaining(
                    new Date().getTime(),
                    new Date(banned_until).getTime()
                );
            }

        },
        mounted(){

            this.setUpObserver();
        }
    });
</script>