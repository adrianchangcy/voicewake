import { createApp } from 'vue';
import { createPinia } from 'pinia';
import piniaPluginPersistedState from 'pinia-plugin-persistedstate';
import { PiniaSharedState } from 'pinia-shared-state';
import VueVirtualScroller from 'vue-virtual-scroller';

import BaseApp from '../src/apps/BaseApp.vue';
import CreateEventsApp from '../src/apps/CreateEventsApp.vue';
import EventReplyChoicesApp from '../src/apps/EventReplyChoicesApp.vue';
import ListUserBannedAudioClipsApp from '../src/apps/ListUserBannedAudioClipsApp.vue';
import ListUserBlocksApp from '../src/apps/ListUserBlocksApp.vue';
import ListUserFollowsApp from '../src/apps/ListUserFollowsApp.vue';
import GetEventsApp from '../src/apps/GetEventsApp.vue';
import BrowseEventsApp from '../src/apps/BrowseEventsApp.vue';
import VUserLogInSignUp from '../src/components/main/VUserLogInSignUp.vue';
import VUserUsername from '../src/components/medium/VUserUsername.vue';
import VBackdropAnime from '../src/components/small/VBackdropAnime.vue';
import TestingStuff from '../src/components/main/TestingStuff.vue';

interface BindingValueTypes {
    refs_to_exclude: string[],
    bool_status_variable_or_callback: boolean|(()=>any),
}


//Pinia
const pinia = createPinia();

//persists store even after browser close/refresh
//you can pass persist:true, or persist:{} at store files
pinia.use(piniaPluginPersistedState);

//sync store across multiple tabs
//at store file level, you can override the settings below
pinia.use(
    PiniaSharedState({
        // Enables the plugin for all stores. Defaults to true.
        enable: false,
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
        element.clickOutsideEventHandler = (event:any) => {

            //unpack passed arguments
            //bool_status_variable_or_callback, string, is the bool status variable, in charge of your element
            //refs_to_exclude, [], means elements that already handle the same bool_status_variable_or_callback variable on their own
            const binding_value:BindingValueTypes = binding.value;

            //contains() on this ref element always returns true when event.target refers to ref child or itself
            //if true, we don't do anything, because excluded element already runs handler at @click
            let is_clicked_element_excluded = false;

            for(let x = 0; x < binding_value.refs_to_exclude.length; x++){

                try{

                    if(binding.instance.$refs[binding_value.refs_to_exclude[x]].contains(event.target)){

                        is_clicked_element_excluded = true;
                        break;
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
            }

            //finally, also check if event.target is outside of our element with this directive attached
            if(
                is_clicked_element_excluded === false &&
                element !== event.target &&
                element.contains(event.target) === false
            ){
                
                //change element's is_open to false manually, because no other way to run methods without binding.value()
                //binding.value() requires that you pass only the method name to the directive
                if(typeof binding_value.bool_status_variable_or_callback === 'string'){

                    binding.instance.$data[binding_value.bool_status_variable_or_callback] = false;

                }else if(typeof binding_value.bool_status_variable_or_callback === 'function'){

                    //callback
                    binding_value.bool_status_variable_or_callback();
                }
            }
        };

        //initially used pointerup instead of click, for preventing v-click-outside on drag
        //but ran into "is_open=true" firing before v-click-outside closes
        //so use click, no issues so far
        document.addEventListener("click", element.clickOutsideEventHandler);
    },
    unmounted: (element:any) => {

        document.removeEventListener("click", element.clickOutsideEventHandler);
    },
};

//as long as base-app has pinia, and since base-app is loaded everywhere, pinia can thus be used everywhere
//the same cannot be said for .directive, nor .component
if(document.querySelector('#base-app')){
    createApp(BaseApp)
        .use(pinia)
        .directive('click-outside', clickOutside)
        .mount('#base-app');
}

//'if' statements for all # might or might not be the most efficient fix
//https://vuejs.org/guide/essentials/application.html#the-root-component

if(document.querySelector('#testing-stuff')){

    createApp(TestingStuff)
        .mount('#testing-stuff');
}

if(document.querySelector('#create-events-app')){

    createApp(CreateEventsApp)
        .mount('#create-events-app');
}

if(document.querySelector('#list-event-choices-app')){

    createApp(EventReplyChoicesApp)
        .directive('click-outside', clickOutside)
        .mount('#list-event-choices-app');
}

if(document.querySelector('#get-events-app')){

    createApp(GetEventsApp)
        .directive('click-outside', clickOutside)
        .mount('#get-events-app');
}

if(document.querySelector('#browse-events-app')){

    createApp(
        BrowseEventsApp,
        {
            propPageContext: 'home',
        }
    ).directive('click-outside', clickOutside)
    .mount('#browse-events-app');
}

if(document.querySelector('#get-user-profile-app')){

    createApp(
        BrowseEventsApp,
        {
            propPageContext: 'user_profile',
        }
    ).directive('click-outside', clickOutside)
    .use(VueVirtualScroller)
    .mount('#get-user-profile-app');
}

if(document.querySelector('#list-user-likes-dislikes-app')){

    createApp(
        BrowseEventsApp,
        {
            propPageContext: 'user_likes_dislikes',
        }
    ).directive('click-outside', clickOutside)
    .mount('#list-user-likes-dislikes-app');
}

if(document.querySelector('#list-user-banned-audio-clips-app')){

    createApp(ListUserBannedAudioClipsApp)
    .mount('#list-user-banned-audio-clips-app');
}

if(document.querySelector('#list-user-blocks-app')){

    createApp(ListUserBlocksApp)
    .mount('#list-user-blocks-app');
}

if(document.querySelector('#list-user-follows-app')){

    createApp(ListUserFollowsApp)
    .mount('#list-user-follows-app');
}

if(document.querySelector('#log-in-page')){

    createApp(
        VUserLogInSignUp,
        {
            propIsForStaticPage: true,
            propRequestedSection: 'log-in-section'
        }
    ).mount('#log-in-page');
}

if(document.querySelector('#sign-up-page')){

    createApp(
        VUserLogInSignUp,
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




