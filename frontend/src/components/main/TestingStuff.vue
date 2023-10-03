<template>
    <div>




    </div>
</template>


<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    // import VActionTextOnly from '../small/VActionTextOnly.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from 'notiwind';
    // import anime from 'animejs';
    // import VPlayback from '../medium/VPlayback.vue';
    // import { useFilteredGroupedEventsStore } from '@/stores/FilteredGroupedEventsStore';
    import GroupedEventsTypes from '@/types/GroupedEvents.interface';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                notifications: [] as any[],
                event_room: null as GroupedEventsTypes|null,
            };
        },
        watch: {
        },
        methods: {
            async callTest() : Promise<void> {
                await axios.get(window.location.origin + '/api/test')
                .then((results:any) => {
                    console.log(results.data);
                });
            },
            async getEventRoom(event_room_id:number) : Promise<void> {

                //prepare events, then separate
                await axios.get(window.location.origin + '/api/events/get/event-room/' + event_room_id.toString())
                .then((results:any) => {

                    if(results.data['data'].length === 0){

                        return;
                    }

                    //API always returns list, even if there is only one event_room
                    this.event_room = results.data['data'][0];
                })
                .catch((error:any) => {

                    notify({
                        title: "Event search failed",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                const token = document.getElementsByName("csrfmiddlewaretoken")[0];

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

            // this.callTest();

            notify({
                title: "Keep it up!",
                text: "You'll finish this project soon. You can do this!",
                type: "ok"
            }, 3000);
        },
    });
</script>