import { createApp } from 'vue';

import BaseApp from './BaseApp.vue';
import ListenCreateEventsApp from './ListenCreateEventsApp.vue';

const clickOutside = {

    beforeMount: (element, binding) => {
        
        element.clickOutsideEvent = event => {

            //unpack passed arguments
            const {related_data,exclude} = binding.value;

            //contains() on this ref element always returns true when event.target refers to ref child or itself
            //if true, we don't do anything, because excluded element already runs handler at @click
            let is_clicked_element_excluded = false;

            exclude.forEach((element)=>{
                
                try{

                    if(binding.instance.$refs[element].contains(event.target)){
                        
                        is_clicked_element_excluded = true;
                    }

                }catch(error){

                    console.log(error);
                    console.log(
                        "Your ref element is probably not available."
                        +" Try putting your ref attribute at an element without v-if and v-show."
                        +" Parent element works if it's purely a container for only this element."
                    );
                }
            });

            //finally, also check if event.target is outside of our element with this directive attached
            if (!is_clicked_element_excluded && element !== event.target && !element.contains(event.target)){
                
                //change to false manually, because no other way to run methods without binding.value()
                //binding.value() requires that you pass only the method name to the directive
                binding.instance.$data[related_data] = false;
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

createApp(BaseApp).directive('click-outside', clickOutside).mount('#base-app');

//this might not be the most efficient fix
//https://vuejs.org/guide/essentials/application.html#the-root-component
if(document.querySelector('#listen-create-events-app')){

    createApp(ListenCreateEventsApp).directive('click-outside', clickOutside).mount('#listen-create-events-app');
}






