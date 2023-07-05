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
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 border-theme-medium-gray shade-border-when-hover focus:border-theme-black"
            />
            <input
                v-for="x in propExtraSlots" :key="x"
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 border-theme-medium-gray shade-border-when-hover focus:border-theme-black"
            />
        </div>
        <div class="h-6 px-2">
            <TransitionFade>
                <div v-show="hasStatusText" class="w-full h-fit text-theme-toast-danger text-base whitespace-break-spaces">
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
                status_text: "",
                new_full_string: "",

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
            }
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
            new_full_string(new_value) : void {

                //we use watcher for emit so we can reduce redundant emit
                //since watchers don't fire when new_value is the same as next new_value
                //e.g. spamming 1 with no change when it is already 111111 will not trigger emit
                if(new_value.length === this.getTotalSlotsQuantity){

                    this.$emit("hasNewValue", new_value);

                }else{

                    this.$emit("hasNewValue", "");
                }
            },
            propTriggerReset() : void {

                this.resetEverything();
            },
        },
        methods: {
            resetEverything() : void {

                this.new_full_string = "";
                this.status_text = "";

                if(this.input_fields === null){

                    return;
                }

                //reset
                this.input_fields.forEach((input_field:Element) => {

                    (input_field as HTMLInputElement).value = "";
                });
            },
            concatenateSlots(input_fields:any) : void {

                //reset
                this.new_full_string = "";

                let concat_string = "";

                input_fields.forEach((input_field:HTMLInputElement) => {

                    if(/^[0-9]+$/.test(input_field.value) === true){
                        
                        concat_string += input_field.value.toString();
                    }
                });

                if(concat_string.length != this.getTotalSlotsQuantity){

                    return;
                }

                this.new_full_string = concat_string;
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

                //check
                if(/^[0-9]+$/.test(pasted_value) === false){

                    this.status_text = "Could not paste '";

                    //shorten the problematic text that the user had pasted
                    if(pasted_value.length > (this.getTotalSlotsQuantity + 3)){

                        this.status_text += pasted_value.slice(0, this.getTotalSlotsQuantity) + "...";

                    }else{

                        this.status_text += pasted_value;
                    }

                    this.status_text += "'.";

                    //reset
                    this.new_full_string = "";
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

                this.concatenateSlots(input_fields);
            },
            handleBackspace(event:KeyboardEvent, current_input_field:HTMLInputElement, current_input_field_index:number) : void {

                const previous_input_field = current_input_field.previousElementSibling as HTMLInputElement;

                //handle backspace
                if(event.key === "Backspace" && current_input_field_index > 0 && current_input_field.value.length === 0){

                    previous_input_field.value = "";
                    previous_input_field.focus();
                    previous_input_field.setSelectionRange(0, previous_input_field.value.length);

                    //reset
                    this.new_full_string = "";
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

                    this.concatenateSlots(input_fields);

                    //handle input position
                    if(current_input_field_index < (input_fields.length - 1)){

                        //go to next input if not last
                        next_input_field.focus();
                        next_input_field.setSelectionRange(0, next_input_field.value.length);
                    }

                }else if(/^[0-9]+$/.test(current_input_field.value) === true){

                    //no valid new manual input, so event.data === null
                    //but current value is valid, e.g. when pasted and programmatically inserted
                    this.concatenateSlots(input_fields);

                }else{

                    //possibly invalid input
                    //normal Backspace when deleting value is also handled here
                    current_input_field.value = "";
                    this.new_full_string = "";
                }
            },
        },
        beforeMount(){
        },
        mounted(){

            //add listeners
            //not declaring as NodeListOf<HTMLInputElement> due to unfixable no-undef warning
            const input_fields = document.querySelectorAll(".number-slot-field > input");
            this.input_fields = input_fields;

            input_fields.forEach((input_field:Element, x:number) => {

                input_field.addEventListener("keydown", (e) => {
                    e.stopPropagation();
                    this.handleBackspace(e as KeyboardEvent, input_field as HTMLInputElement, x);
                    this.status_text = "";
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
                    this.handleBackspace(e as KeyboardEvent, input_field as HTMLInputElement, x);
                    this.status_text = "";
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