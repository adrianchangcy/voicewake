import { createApp } from 'vue';
import { createPinia } from 'pinia';
import piniaPluginPersistedState from 'pinia-plugin-persistedstate';
import { PiniaSharedState } from 'pinia-shared-state';

import BaseApp from '/src/apps/BaseApp.vue';
import CreateEventRoomsApp from '/src/apps/CreateEventRoomsApp.vue';
import ListEventRoomChoicesApp from '/src/apps/ListEventRoomChoicesApp.vue';
import ListUserBannedEventsApp from '/src/apps/ListUserBannedEventsApp.vue';
import ListUserBlocksApp from '/src/apps/ListUserBlocksApp.vue';
import GetEventRoomsApp from '/src/apps/GetEventRoomsApp.vue';
import BrowseEventRoomsApp from '/src/apps/BrowseEventRoomsApp.vue';
import UserLogInSignUp from '/src/components/main/UserLogInSignUp.vue';
import VUserUsername from '/src/components/medium/VUserUsername.vue';
import VBackdropAnime from '/src/components/small/VBackdropAnime.vue';


const pinia = createPinia();

//persists store even after browser close/refresh
//you can pass persist:true, or persist:{} at store files
pinia.use(piniaPluginPersistedState);

//sync store across multiple tabs
//at store file level, you can override the settings below
pinia.use(
    PiniaSharedState({
        // Enables the plugin for all stores. Defaults to true.
        enable: true,
        // If set to true this tab tries to immediately recover the shared state from another tab. Defaults to true.
        initialize: false,
        // Enforce a type. One of native, idb, localstorage or node. Defaults to native.
        type: 'localstorage',
    }),
);

const clickOutside = {

    //PROBLEM: make anything with v-click-outside to treat other v-click-outside like any other elements
    //FIX: don't use event.stopPropagation(), else your events cannot reach here

    beforeMount: (element:any, binding:any) => {

        //2022-12-28
        //QUESTION: where did event come from?
        element.clickOutsideEvent = (event:any) => {

            //unpack passed arguments
            //var_name_for_element_bool_status, string, is the bool status variable, in charge of your element
            //refs_to_exclude, [], means elements that already handle the same var_name_for_element_bool_status variable on their own
            const {var_name_for_element_bool_status, refs_to_exclude} = binding.value;

            //contains() on this ref element always returns true when event.target refers to ref child or itself
            //if true, we don't do anything, because excluded element already runs handler at @click
            let is_clicked_element_excluded = false;

            refs_to_exclude.forEach((ref_name:any)=>{

                try{

                    if(binding.instance.$refs[ref_name].contains(event.target)){
                        
                        is_clicked_element_excluded = true;
                    }

                }catch(error){

                    console.log(error);
                    console.log(
                        "Your excluded ref element is probably not available when referenced."
                        +" Your element to exclude for ref must be static and not Vue-generated."
                        +" An easy fix is to wrap your excluded element in another div, and put your ref at this now-sibling div."
                        +" With this now-sibling div, avoid styling it so it wraps its child completely."
                    );
                }
            });

            //finally, also check if event.target is outside of our element with this directive attached
            if(
                is_clicked_element_excluded === false &&
                element !== event.target &&
                element.contains(event.target) === false
            ){
                
                //change element's is_open to false manually, because no other way to run methods without binding.value()
                //binding.value() requires that you pass only the method name to the directive
                if(typeof var_name_for_element_bool_status === 'string'){

                    binding.instance.$data[var_name_for_element_bool_status] = false;

                }else{

                    //callback
                    var_name_for_element_bool_status();
                }
            }
        };

        //use mousedown and not click, since click also listens to mouseup
        //we don't want to trigger mouseup on window drag (e.g. slider)
        document.addEventListener("pointerup", element.clickOutsideEvent);
    },
    unmounted: (element:any) => {

        document.removeEventListener("pointerup", element.clickOutsideEvent);
    },
};

//as long as base-app has pinia, and since base-app is loaded everywhere, pinia can thus be used everywhere
//the same cannot be said for click-outside
createApp(BaseApp)
    .use(pinia)
    .directive('click-outside', clickOutside)
    .mount('#base-app');

//if-else for all # might or might not be the most efficient fix
//https://vuejs.org/guide/essentials/application.html#the-root-component
if(document.querySelector('#create-event-rooms-app')){

    createApp(CreateEventRoomsApp)
        .mount('#create-event-rooms-app');
}

if(document.querySelector('#list-event-room-choices-app')){

    createApp(ListEventRoomChoicesApp)
        .directive('click-outside', clickOutside)
        .mount('#list-event-room-choices-app');
}

if(document.querySelector('#get-event-rooms-app')){

    createApp(GetEventRoomsApp)
        .directive('click-outside', clickOutside)
        .mount('#get-event-rooms-app');
}

if(document.querySelector('#browse-event-rooms-app')){

    createApp(BrowseEventRoomsApp)
        .directive('click-outside', clickOutside)
        .mount('#browse-event-rooms-app');
}

if(document.querySelector('#get-user-profile-app')){

    createApp(
        BrowseEventRoomsApp,
        {
            propIsUserProfilePage: true
        }
    ).directive('click-outside', clickOutside)
    .mount('#get-user-profile-app');
}

if(document.querySelector('#list-user-banned-events-app')){

    createApp(ListUserBannedEventsApp)
        .mount('#list-user-banned-events-app');
}

if(document.querySelector('#list-user-blocks-app')){

    createApp(ListUserBlocksApp)
        .mount('#list-user-blocks-app');
}

if(document.querySelector('#log-in-page')){

    createApp(
        UserLogInSignUp,
        {
            propIsForStaticPage: true,
            propRequestedSection: 'log-in-section'
        }
    ).mount('#log-in-page');
}

if(document.querySelector('#sign-up-page')){

    createApp(
        UserLogInSignUp,
        {
            propIsForStaticPage: true,
            propRequestedSection: 'sign-up-section'
        }
    ).mount('#sign-up-page');
}

if(document.querySelector('#set-username-page')){

    createApp(VUserUsername)
        .mount('#set-username-page');
}

if(document.querySelector('#v-backdrop-anime-target')){

    createApp(VBackdropAnime)
        .mount('#v-backdrop-anime-target');
}




