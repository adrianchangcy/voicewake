import { createApp } from 'vue';
import { mixinGeneral } from './mixin_general.js';

import BaseApp from './BaseApp.vue';
import CreateMainEventsApp from './CreateMainEventsApp.vue';

const clickOutside = {

    //2022-12-28
    //ARCHIVED TO-DO: make anything with v-click-outside to treat other v-click-outside like any other elements
        //v-click-outside's element scope is on individual component level
        //so when clicking via cross-component, it doesn't register
        //PROBLEM: is_open does not become false if clicking another v-click-outside component

    beforeMount: (element, binding) => {

        //2022-12-28
        //QUESTION: where did event come from?
        element.clickOutsideEvent = event => {

            //unpack passed arguments
            //var_name_for_element_bool_status, string, is the bool status variable, in charge of your element
            //refs_to_exclude, [], means elements that already handle the same var_name_for_element_bool_status variable on their own
            const {var_name_for_element_bool_status, refs_to_exclude} = binding.value;

            //contains() on this ref element always returns true when event.target refers to ref child or itself
            //if true, we don't do anything, because excluded element already runs handler at @click
            let is_clicked_element_excluded = false;

            refs_to_exclude.forEach((ref_name)=>{

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

        document.addEventListener("click", element.clickOutsideEvent);
        document.addEventListener("touchstart", element.clickOutsideEvent);
    },
    unmounted: element => {

        document.removeEventListener("click", element.clickOutsideEvent);
        document.removeEventListener("touchstart", element.clickOutsideEvent);
    },
};

createApp(BaseApp)
    .directive('click-outside', clickOutside)
    .mount('#base-app');

//this might not be the most efficient fix
//https://vuejs.org/guide/essentials/application.html#the-root-component
if(document.querySelector('#create-main-events-app')){

    createApp(CreateMainEventsApp)
        .directive('click-outside', clickOutside)
        .mixin(mixinGeneral)
        .mount('#create-main-events-app');

}






