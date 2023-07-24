<template>
    <div>
        <VInputLabel :for="propElementId">
            <span>{{ propLabelText }}</span>
        </VInputLabel>
        <!--pattern attribute does not help-->
        <div class="number-slot-field h-10 flex flex-row gap-1 text-xl">
            <input
                :id="propElementId"
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 focus:border-theme-black border-theme-medium-gray shade-border-when-hover     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-black"
            />
            <input
                v-for="x in propExtraSlots" :key="x"
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 focus:border-theme-black border-theme-medium-gray shade-border-when-hover     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-black"
            />
        </div>
        <div class="h-6 px-2">
            <TransitionFade>
                <div v-show="is_error" class="w-full h-fit text-theme-toast-danger text-base whitespace-break-spaces">
                    <p>{{ status_text }}</p>
                </div>
            </TransitionFade>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VInputLabel from '@/components/small/VInputLabel.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
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

                input_fields: null as any,  //NodeListOf<Element> from querySelectorAll() is undefined
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
            concatenateSlots(input_fields:any) : void {

                let concat_string = "";

                input_fields.forEach((input_field:HTMLInputElement) => {

                    if(/^[0-9]+$/.test(input_field.value) === true){
                        
                        concat_string += input_field.value.toString();
                    }
                });

                this.otp_string = concat_string;
            },
            handlePaste(event:ClipboardEvent, input_fields:any) : void {

                //thanks to Lighthouse for discovering this when analysing
                if(event.clipboardData === null){

                    return;
                }

                //remove spaces
                //getData() returns "" if there is nothing
                //we don't want to use deep-clean with regex here, so that user can identify their mistake
                const pasted_value:string = (event.clipboardData as DataTransfer).getData("text/plain").replace(/\s/g, "");

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

                    this.concatenateSlots(input_fields);
                    return;
                }

                let last_filled_input_index = 0;

                //can continue, so insert
                for(let x = 0; x < input_fields.length; x++){

                    if(x < pasted_value.length){

                        input_fields[x].value = pasted_value[x];
                        last_filled_input_index = x;

                    }else{

                        input_fields[x].value = "";
                    }
                }
                
                //focus on last character of pasted input, or last slot
                input_fields[last_filled_input_index].focus();
                input_fields[last_filled_input_index].setSelectionRange(input_fields[last_filled_input_index].value.length, input_fields[last_filled_input_index].value.length);

                this.resetErrorMessage();
                this.concatenateSlots(input_fields);
            },
            handleBackspace(event:KeyboardEvent, input_fields:any, current_input_field:HTMLInputElement, current_input_field_index:number) : void {

                const previous_input_field = current_input_field.previousElementSibling as HTMLInputElement;

                //handle backspace
                if(event.key === "Backspace" && current_input_field_index > 0 && current_input_field.value.length === 0){

                    previous_input_field.value = "";
                    previous_input_field.focus();
                    previous_input_field.setSelectionRange(0, previous_input_field.value.length);

                    //reset
                    this.resetErrorMessage();
                    this.concatenateSlots(input_fields);
                    return;
                }
            },
            validateSlot(
                event:InputEvent, input_fields:any, current_input_field:HTMLInputElement, current_input_field_index:number
            ) : void {

                // This code gets the current input element and stores it in the currentInput variable
                // This code gets the next sibling element of the current input element and stores it in the nextInput variable
                // This code gets the previous sibling element of the current input element and stores it in the prevInput variable
                const next_input_field = current_input_field.nextElementSibling as HTMLInputElement;

                //prevent > 1 number
                if(current_input_field.value.length > 1){

                    current_input_field.value = "";
                    return;
                }

                //handle validation
                if(/^[0-9]+$/.test(event.data!) === true){

                    //has valid new manual input
                    current_input_field.value = event.data!;

                    //put this here to avoid resetting error message of handlePaste()
                    //since paste event also triggers input event
                    this.resetErrorMessage();

                    //handle input position
                    if(current_input_field_index < (input_fields.length - 1)){

                        //go to next input if not last
                        next_input_field.focus();
                        next_input_field.setSelectionRange(0, next_input_field.value.length);
                    }

                }else{

                    //possibly invalid input
                    //normal Backspace when deleting value is also handled here
                    current_input_field.value = "";
                }

                this.concatenateSlots(input_fields);
            },
        },
        mounted(){

            //add listeners
            //not declaring as NodeListOf<HTMLInputElement> due to unfixable no-undef warning
            const input_fields = document.querySelectorAll(".number-slot-field > input");
            this.input_fields = input_fields;

            input_fields.forEach((input_field:Element, x:number) => {

                input_field.addEventListener("keydown", (e) => {
                    e.stopPropagation();
                    this.handleBackspace(e as KeyboardEvent, input_fields, input_field as HTMLInputElement, x);
                });
                input_field.addEventListener("input", (e) => {
                    e.stopPropagation();
                    this.validateSlot(e as InputEvent, input_fields, input_field as HTMLInputElement, x);
                });
                input_field.addEventListener("click", (e) => {
                    e.stopPropagation();
                    (input_field as HTMLInputElement).setSelectionRange(0, (input_field as HTMLInputElement).value.length);
                });
            });

            input_fields[0].addEventListener("paste", (e) => {
                this.handlePaste(e as ClipboardEvent, input_fields);
            });
        },
        beforeUnmount(){

            //remove listeners
            const input_fields = document.querySelectorAll(".number-slot-field > input");

            input_fields.forEach((input_field, x) => {

                input_field.removeEventListener("keydown", (e) => {
                    e.stopPropagation();
                    this.handleBackspace(e as KeyboardEvent,input_fields, input_field as HTMLInputElement, x);
                });
                input_field.removeEventListener("input", (e) => {
                    e.stopPropagation();
                    this.validateSlot(e as InputEvent, input_fields, input_field as HTMLInputElement, x);
                });
                input_field.removeEventListener("click", (e) => {
                    e.stopPropagation();
                    (input_field as HTMLInputElement).setSelectionRange(0, (input_field as HTMLInputElement).value.length);
                });
            });

            input_fields[0].removeEventListener("paste", (e) => {
                this.handlePaste(e as ClipboardEvent, input_fields);
            });
        },
    });
</script>