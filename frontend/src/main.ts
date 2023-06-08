import { createApp } from 'vue';

import NavBarApp from '/src/apps/NavBarApp.vue';
import CreateEventRoomsApp from '/src/apps/CreateEventRoomsApp.vue';
import ListEventRoomsApp from '/src/apps/ListEventRoomsApp.vue';
import GetEventRoomsApp from '/src/apps/GetEventRoomsApp.vue';
import UserOptionsApp from '/src/apps/UserOptionsApp.vue';

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
                binding.instance.$data[var_name_for_element_bool_status] = false;
            }
        };

        //use mousedown and not click, since click also listens to mouseup
        //we don't want to trigger mouseup on window drag (e.g. slider)
        document.addEventListener("mousedown", element.clickOutsideEvent);
        document.addEventListener("touchstart", element.clickOutsideEvent);
    },
    unmounted: (element:any) => {

        document.removeEventListener("mousedown", element.clickOutsideEvent);
        document.removeEventListener("touchstart", element.clickOutsideEvent);
    },
};

createApp(NavBarApp)
    .directive('click-outside', clickOutside)
    .mount('#nav-bar-app');

//this might not be the most efficient fix
//https://vuejs.org/guide/essentials/application.html#the-root-component
if(document.querySelector('#create-event-rooms-app')){

    createApp(CreateEventRoomsApp)
        .directive('click-outside', clickOutside)
        .mount('#create-event-rooms-app');
}

if(document.querySelector('#list-event-rooms-app')){

    createApp(ListEventRoomsApp)
        .directive('click-outside', clickOutside)
        .mount('#list-event-rooms-app');
}

if(document.querySelector('#get-event-rooms-app')){

    createApp(GetEventRoomsApp)
        .directive('click-outside', clickOutside)
        .mount('#get-event-rooms-app');
}

if(document.querySelector('#user-options-app')){

    createApp(UserOptionsApp)
        .directive('click-outside', clickOutside)
        .mount('#user-options-app');
}





