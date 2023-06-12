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
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 border-theme-medium-gray focus:border-theme-black"
            />
            <input
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 border-theme-medium-gray focus:border-theme-black"
            />
            <input
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 border-theme-medium-gray focus:border-theme-black"
            />
            <input
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 border-theme-medium-gray focus:border-theme-black"
            />
            <input
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 border-theme-medium-gray focus:border-theme-black"
            />
            <input
                type="text" inputmode="numeric" maxlength="1" autocomplete="off"
                name="number-slot-field"
                class="w-10 h-full bg-theme-light text-center py-1 rounded-lg border-2 border-theme-medium-gray focus:border-theme-black"
            />
        </div>
        <TransitionFade>
            <div v-show="hasStatusText" class="w-full h-fit text-theme-toast-danger text-base whitespace-break-spaces">
                <p>{{ status_text }}</p>
            </div>
        </TransitionFade>

        <!--empty block to keep spacing consistent-->
        <div class="w-0 h-6">
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
                slot_quantity: 6,   //too lazy to dynamically set this with prop, due to DOM being a headache with listeners
                new_full_string: "",
                current_focused_input_index: 0,
            };
        },
        props: {
            propElementId: String,
            propLabelText: String,
        },
        emits: ["hasNewValue"],
        computed: {
            hasStatusText() : boolean {
                return this.status_text.length > 0;
            },
        },
        watch: {
            new_full_string(new_value) : void {

                //we use watcher for emit so we can reduce redundant emit
                //since watchers don't fire when new_value is the same as next new_value
                //e.g. spamming 1 with no change when it is already 111111 will not trigger emit
                if(new_value.length === this.slot_quantity){

                    this.$emit("hasNewValue", new_value);

                }else{

                    this.$emit("hasNewValue", "");
                }
            },
        },
        methods: {
            concatenateSlots(input_fields:any) : void {

                //reset
                this.new_full_string = "";

                let concat_string = "";

                input_fields.forEach((input_field:HTMLInputElement) => {

                    if(/^[0-9]+$/.test(input_field.value) === true){
                        
                        concat_string += input_field.value.toString();
                    }
                });

                this.new_full_string = concat_string;
            },
            handlePaste(event:ClipboardEvent, input_fields:any) : void {

                //remove spaces
                //getData() returns "" if there is nothing
                //we don't want to use deep-clean with regex here, so that user can identify their mistake
                const pasted_value:string = (event.clipboardData as DataTransfer).getData("text/plain").replace(/\s/g, "");

                //check
                if(/^[0-9]+$/.test(pasted_value) === false){

                    this.status_text = "The code must have only " + this.slot_quantity.toString() + " numbers.\nWhat you had copied: ";

                    if(pasted_value.length > (this.slot_quantity + 3)){

                        this.status_text += pasted_value.slice(0, this.slot_quantity) + "...";

                    }else{

                        this.status_text += pasted_value;
                    }

                    this.concatenateSlots(input_fields);
                    return;
                }

                let last_filled_input_index = 0;

                //insert
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
            handleBackspace(event:KeyboardEvent, input_fields:any, current_input_field:HTMLInputElement, current_input_field_index:number) : void {

                const previous_input_field = current_input_field.previousElementSibling as HTMLInputElement;

                //handle backspace
                if(event.key === "Backspace" && current_input_field_index > 0 && current_input_field.value.length === 0){

                    previous_input_field.value = "";
                    previous_input_field.focus();
                    previous_input_field.setSelectionRange(0, previous_input_field.value.length);

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

                //concatenate early to also emit "" on error
                this.concatenateSlots(input_fields);

                //prevent > 1 number
                if(current_input_field.value.length > 1){

                    current_input_field.value = "";
                    return;
                }

                //handle validation
                if(/^[0-9]+$/.test(event.data!) === true){

                    //ok
                    current_input_field.value = event.data!;

                }else if(/^[0-9]+$/.test(current_input_field.value) === true){

                    //invalid input on current valid value
                    return;

                }else{

                    //invalid input on current invalid value
                    current_input_field.value = "";
                    return;
                }

                //handle input position
                if(current_input_field_index < (input_fields.length - 1)){

                    //go to next input if not last
                    next_input_field.focus();
                    next_input_field.setSelectionRange(0, next_input_field.value.length);
                    return;
                }
            },
        },
        beforeMount(){
        },
        mounted(){

            //add listeners
            //not declaring as NodeListOf<HTMLInputElement> due to unfixable no-undef warning
            const input_fields = document.querySelectorAll(".number-slot-field > input");

            input_fields.forEach((input_field:Element, x:number) => {

                input_field.addEventListener("keydown", (e) => {
                    e.stopPropagation();
                    this.handleBackspace(e as KeyboardEvent, input_fields, input_field as HTMLInputElement, x);
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

            //focus the first input which index is 0 on mounted
            (input_fields[0] as HTMLInputElement).focus();
        },
        beforeUnmount(){

            //remove listeners
            const input_fields = document.querySelectorAll(".number-slot-field > input");

            input_fields.forEach((input_field, x) => {

                input_field.removeEventListener("keydown", (e) => {
                    e.stopPropagation();
                    this.handleBackspace(e as KeyboardEvent, input_fields, input_field as HTMLInputElement, x);
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