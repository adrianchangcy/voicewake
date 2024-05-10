<template>
    <div>
        <VInputLabel :for="propElementId">
            <span>{{ propLabelText }}</span>
        </VInputLabel>
        <!--pattern attribute does not help-->
        <div class="number-slot-field h-10 flex flex-row items-center gap-1 text-lg">
            <input
                :id="propElementId"
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                :data-index="0"
                class="w-10 h-full bg-theme-light dark:bg-theme-dark text-center py-1 rounded-lg border-2 focus:border-theme-black dark:focus:border-dark-theme-white-2 border-theme-gray-form-field dark:border-dark-theme-gray-form-field shade-border-when-hover    focus:outline-none"
            />
            <input
                v-for="x in propExtraSlots" :key="x"
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                :data-index="x"
                class="w-10 h-full bg-theme-light dark:bg-theme-dark text-center py-1 rounded-lg border-2 focus:border-theme-black dark:focus:border-dark-theme-white-2 border-theme-gray-form-field dark:border-dark-theme-gray-form-field shade-border-when-hover    focus:outline-none"
            />
            <FontAwesomeIcon v-show="is_error" icon="fas fa-exclamation" class="px-2 text-red-700 dark:text-red-400"/>
        </div>
        <div class="h-6">
            <TransitionFade>
                <div v-show="is_error" class="h-fit text-red-700 dark:text-red-400 text-base whitespace-break-spaces">
                    <span>{{ status_text }}</span>
                </div>
            </TransitionFade>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VInputLabel from '../small/VInputLabel.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faExclamation } from '@fortawesome/free-solid-svg-icons/faExclamation';

    library.add(faExclamation);
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        name: "UserOptionsApp",
        data() {
            return {
                otp_string: "",

                is_error: false,
                status_text: "",

                //unable to type NodeListOf successfully, so we just call it once
                //data() calls before mounted(), so don't expect elements here yet
                input_fields: document.querySelectorAll(".number-slot-field > input"),
            };
        },
        props: {
            propElementId: String,
            propLabelText: String,
            propExtraSlots: {
                type: Number,
                required: true
            },
            propTriggerReset: { //use this to reset the slots, regardless of true/false
                type: Boolean
            },
            propIsError: {
                type: Boolean
            },
            propStatusText: {
                type: String
            },
        },
        emits: ["hasNewValue"],
        computed: {
            getTotalSlotsQuantity() : number {

                return this.propExtraSlots + 1;
            },
            hasStatusText() : boolean {

                return this.status_text.length > 0;
            },
        },
        watch: {
            propIsError(new_value){

                this.is_error = new_value;
            },
            propStatusText(new_value){

                this.status_text = new_value;
            },
            otp_string(new_value){

                this.$emit("hasNewValue", new_value);
            },
            propTriggerReset() : void {

                this.resetEverything();
            },
        },
        methods: {
            resetEverything() : void {

                this.otp_string = "";
                this.is_error = false;
                this.status_text = "";

                if(this.input_fields === null){

                    return;
                }

                //reset
                this.input_fields.forEach((input_field:Element) => {

                    (input_field as HTMLInputElement).value = "";
                });
            },
            resetErrorMessage() : void {

                //need this to be separated from concatenateSlots(), as shown in handlePaste() as use case
                this.is_error = false;
                this.status_text = "";
            },
            concatenateSlots() : void {

                let concat_string = "";

                this.input_fields.forEach((element:Element)=>{

                    if(/^[0-9]+$/.test((element as HTMLInputElement).value) === true){
                        
                        concat_string += (element as HTMLInputElement).value.toString();
                    }
                });

                this.otp_string = concat_string;
            },
            handlePaste(event:Event) : void {

                //thanks to Lighthouse for discovering possible .clipboardData === null when analysing
                const clipboard_data = (event as ClipboardEvent).clipboardData;

                if(clipboard_data === null){

                    return;
                }

                //remove spaces
                //getData() returns "" if there is nothing
                //we don't want to use deep-clean with regex here, so that user can identify their mistake
                const pasted_value:string = (clipboard_data as DataTransfer).getData("text/plain").replace(/\s/g, "");

                //check and override error message
                if(/^[0-9]+$/.test(pasted_value) === false){

                    this.is_error = true;
                    this.status_text = "Could not paste '";

                    //shorten the problematic text that the user had pasted
                    if(pasted_value.length > (this.getTotalSlotsQuantity + 3)){

                        this.status_text += pasted_value.slice(0, this.getTotalSlotsQuantity) + "..";

                    }else{

                        this.status_text += pasted_value;
                    }

                    this.status_text += "'.";

                    this.concatenateSlots();
                    return;
                }

                let last_filled_input_index = 0;

                //can continue, so start pasting programmatically
                //during this, if input_fields[x] is going over pasted_value.length, "" is pasted instead
                for(let x = 0; x < this.input_fields.length; x++){

                    if(x < pasted_value.length){

                        (this.input_fields[x] as HTMLInputElement).value = pasted_value[x];
                        last_filled_input_index = x;

                    }else{

                        (this.input_fields[x] as HTMLInputElement).value = "";
                    }
                }
                
                //focus on last character of pasted input
                //input listener only triggers for last slot, with e.data===null and current_input_field.value!=null
                //input listener will not trigger for every slot before the last one if done in for-loop above
                const last_input_field = this.input_fields[last_filled_input_index] as HTMLInputElement;

                last_input_field.focus();
                last_input_field.setSelectionRange(
                    last_input_field.value.length,
                    last_input_field.value.length
                );

                this.resetErrorMessage();
                this.concatenateSlots();
            },
            handleBackspace(event:Event) : void {

                const current_input_field = (event.currentTarget as HTMLInputElement);
                const previous_input_field = current_input_field.previousElementSibling as HTMLInputElement;
                const current_index = Number(current_input_field.getAttribute('data-index')!);

                //handle backspace
                if(
                    (event as KeyboardEvent).key === "Backspace" &&
                    current_index > 0 &&
                    current_input_field.value.length === 0
                ){

                    previous_input_field.value = "";
                    previous_input_field.focus();
                    previous_input_field.setSelectionRange(0, previous_input_field.value.length);

                    //reset
                    this.resetErrorMessage();
                    this.concatenateSlots();
                }
            },
            validateSlot(event:Event) : void {

                //current_input_field behaves as reference
                    //when manual user input, current_input_field.value!=null, e.data!=null
                    //when programmatically inserted input, current_input_field.value!=null, e.data===null

                //null if not found
                const current_input_field = (event.currentTarget as HTMLInputElement);
                const next_input_field = current_input_field.nextElementSibling as HTMLInputElement;
                const current_index = Number(current_input_field.getAttribute('data-index')!);
                
                //get the value in the context of slot that triggered validateSlot()
                //irrelevant reminder that typeof null is object, not "null type"
                let new_slot_value = "";
                const input_data = (event as InputEvent).data;

                if(input_data !== null && input_data.length > 0){

                    new_slot_value = input_data;

                }else if(current_input_field.value !== null && current_input_field.value.length > 0){

                    new_slot_value = current_input_field.value;
                }

                //prevent > 1 number
                if(current_input_field.value.length > 1){

                    current_input_field.value = "";
                    return;
                }

                //handle validation
                if(/^[0-9]+$/.test(new_slot_value) === true){

                    //has valid input

                    //put this here to avoid resetting error message of handlePaste()
                    //since paste e also triggers input e
                    this.resetErrorMessage();

                    //handle input position
                    if(next_input_field !== null && current_index < (this.input_fields.length - 1)){

                        //go to next input if not last
                        next_input_field.focus();
                        next_input_field.setSelectionRange(0, next_input_field.value.length);
                    }

                }else{

                    //possibly invalid input
                    //normal Backspace when deleting value is also handled here
                    current_input_field.value = "";
                }

                this.concatenateSlots();
            },
            selectEntireInput(event:Event) : void {

                event.stopPropagation();

                const current_input_field = event.currentTarget as HTMLInputElement;

                current_input_field.setSelectionRange(0, current_input_field.value.length);
            },
        },
        mounted(){

            //add listeners
            this.input_fields = document.querySelectorAll(".number-slot-field > input");

            this.input_fields.forEach((input_field:Element) => {

                input_field.addEventListener("keydown", this.handleBackspace);
                input_field.addEventListener("input", this.validateSlot);
                input_field.addEventListener("click", this.selectEntireInput);
            });

            this.input_fields[0].addEventListener("paste", this.handlePaste);
        },
        beforeUnmount(){

            //remove listeners
            this.input_fields.forEach((input_field:Element) => {

                input_field.removeEventListener("keydown", this.handleBackspace);
                input_field.removeEventListener("input", this.validateSlot);
                input_field.removeEventListener("click", this.selectEntireInput);
            });

            this.input_fields[0].removeEventListener("paste", this.handlePaste);
        },
    });
</script>