import { createApp } from 'vue';

import BaseApp from './BaseApp.vue';

const clickOutside = {
    
    beforeMount: (element, binding) => {
        
        element.clickOutsideEvent = event => {

            //unpack passed arguments
            const {related_data,exclude} = binding.value;

            //contains() on this ref element always returns true when event.target refers to ref child or itself
            //if true, we don't want to run handler, because excluded element already runs handler at @click
            let is_clicked_element_excluded = binding.instance.$refs[exclude].contains(event.target);

            //finally, also check if event.target is outside of our element with this directive attached
            if (!is_clicked_element_excluded && element !== event.target && !element.contains(event.target)){
                
                //change to false manually, because no other way to run methods without binding.value()
                //binding.value() requires that you pass only the method name to the directive
                binding.instance.$data[related_data] = false;
            }
        };

      document.addEventListener("click", element.clickOutsideEvent);
    },
    unmounted: element => {

      document.removeEventListener("click", element.clickOutsideEvent);
    },
};

createApp(BaseApp).directive('click-outside', clickOutside).mount('#base-app');






