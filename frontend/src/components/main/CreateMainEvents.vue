<template>

    <div class="md:w-2/4 lg:w-3/6 xl:w-2/6 mx-auto h-fit bg-theme-light text-left text-lg px-[5%] pb-20">

        <VSectionTitle
            propTitle="Say"
            propTitleDescription="Fill in the fields below"
        />

        <form
            spellcheck="false"
            class="bg-theme-light flex flex-col gap-4 text-theme-black"
        >
            <!--title-->
            <VTextArea
                :propIsRequired="true"
                propElementId="event-name"
                propLabel="Title"
                propPlaceholder=""
                :propMaxLength="40"
                :propHasTextCounter="true"
                :propHasStatusText="false"
                @newValue="handleNewEventName($event)"
            />

            <!--fields for open/close-->
            <div class="grid grid-cols-7 gap-2">

                <!--open/close VEventToneMenu-->
                <div ref="event_tone_field" class="col-span-2">
                    <VEventToneField
                        propLabel="Feeling"
                        :propEventToneChoice="event_tone_choice"
                        :propIsOpen="is_event_tone_menu_open"
                        @isOpen="handleIsEventToneMenuOpen($event)"
                    />
                </div>

                <!--open/close VRecorderMenu-->
                <div ref="recorder_field" class="col-span-5">
                    <VRecorderField
                        propLabel="Your voice"
                        :propIsOpen="is_recorder_menu_open"
                        :propBucketQuantity="bucket_quantity"
                        :propHasRecording="final_blob !== null"
                        :propFileVolumes="blob_volume_peaks"
                        :propFileDuration="blob_duration"
                        @isOpen="handleIsRecorderMenuOpen($event)"
                    />
                </div>
            </div>

            <!--menus-->
            <div class="w-full h-fit relative">

                <!--arrows, aesthetics only-->
                <div class="w-full h-0 grid grid-cols-7 gap-4">
                    <!--arrow for event_tones menu-->
                    <div v-show="is_event_tone_menu_open" class="col-span-2 col-start-1 relative">
                        <div class="z-10 w-2 h-2 absolute -top-1 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"></div>
                    </div>
                    <!--arrow for recorder menu-->
                    <div v-show="is_recorder_menu_open" class="col-span-5 col-start-3 relative">
                        <div class="z-10 w-2 h-2 absolute -top-1 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"></div>
                    </div>
                </div>

                <!--event_tone menu-->
                <div
                    v-click-outside="{
                        var_name_for_element_bool_status: 'is_event_tone_menu_open',
                        refs_to_exclude: ['event_tone_field', 'recorder_field']
                    }"
                >
                    <VEventToneMenu
                        :propIsOpen="is_event_tone_menu_open"
                        @eventToneSelected="handleEventToneSelected($event)"
                        class="border-2 border-theme-black rounded-lg"
                    />
                </div>

                <!--recorder menu-->
                <div
                    v-click-outside="{
                        var_name_for_element_bool_status: 'is_recorder_menu_open',
                        refs_to_exclude: ['event_tone_field', 'recorder_field']
                    }"
                >
                    <VRecorderMenu
                        :propIsOpen="is_recorder_menu_open"
                        :propBucketQuantity="bucket_quantity"
                        :propMaxDuration="max_duration"
                        @newRecording="handleNewRecording($event)"
                        class="border-2 border-theme-black rounded-lg"
                    />
                </div>
            </div>

            <!--submit-->
            <div class="py-4">
                <VActionButtonBig
                    class="mx-auto"
                    :propIsEnabled="canSubmit"
                    @click.stop="submitForm()"
                >
                    <span>Done</span>
                </VActionButtonBig>
            </div>

        </form>

    </div>
</template>


<script setup lang="ts">

    import VActionButtonBig from '/src/components/small/VActionButtonBig.vue';
    import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VTextArea from '/src/components/small/VTextArea.vue';
    import VEventToneField from '/src/components/medium/VEventToneField.vue';
    import VEventToneMenu from '/src/components/medium/VEventToneMenu.vue';
    import VRecorderField from '/src/components/medium/VRecorderField.vue';
    import VRecorderMenu from '/src/components/medium/VRecorderMenu.vue';

</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import EventToneTypes from '@/types/EventTones.interface';
    const axios = require('axios');

    export default defineComponent({
        data() {
            return {

                event_name: "",

                is_event_tone_menu_open: false, //updates only from VEventToneField to VEventToneMenu, maybe use vuex
                event_tone_choice: null as EventToneTypes|null,

                is_recorder_menu_open: false,
                final_blob: null as Blob|null,
                blob_duration: 0,
                blob_volume_peaks: [] as number[],
                bucket_quantity: 20,
                // propMaxDuration: (1000 * 60 * 2) + 500,    //2m + 0.5s, as final_blob is always +-0.1s away
                max_duration: 10000,    //2m + 0.5s, as final_blob is always +-0.1s away
            };
        },
        watch: {
            is_event_tone_menu_open(new_value){

                if(new_value === true && this.is_recorder_menu_open === true){

                    this.is_recorder_menu_open = false;
                }
            },
            is_recorder_menu_open(new_value){
                
                if(new_value === true && this.is_event_tone_menu_open === true){

                    this.is_event_tone_menu_open = false;
                }
            },
        },
        computed: {
            canSubmit() : boolean {

                if(
                    this.event_name.trim() !== '' &&
                    this.event_tone_choice !== null &&
                    this.final_blob !== null
                ){

                    return true;
                }

                return false;
            },
        },
        mounted(){

            //set up axios appropriately
            this.axiosSetup();
        },
        methods: {
            async submitForm() : Promise<void> {

                if(this.canSubmit === false){

                    return;
                }

                let data = new FormData();
                
                data.append("event_name", this.event_name);
                data.append("event_tone_id", (this.event_tone_choice as EventToneTypes)['id'].toString());
                data.append("audio_file", this.final_blob as Blob);

                axios.post('say', data)
                .then((response:any) => console.log(response))
                .catch((errors:any) => console.log(errors));
            },
            handleNewRecording(new_value:{'blob':Blob, 'blob_duration':number, 'blob_volume_peaks':number[]}) : void {

                this.final_blob = new_value['blob'];
                this.blob_duration = new_value['blob_duration'];
                this.blob_volume_peaks = new_value['blob_volume_peaks'];
            },
            handleIsRecorderMenuOpen(new_value:boolean) : void {

                this.is_recorder_menu_open = new_value;
            },
            handleEventToneSelected(new_value:EventToneTypes) : void {

                this.is_event_tone_menu_open = false;
                this.event_tone_choice = new_value;
            },
            handleIsEventToneMenuOpen(new_value:boolean) : void {

                this.is_event_tone_menu_open = new_value;
            },
            handleNewEventName(new_value:string) : void {

                this.event_name = new_value;
            },
            handleSubmit(): void {
                console.log("y submit? lol");
            },
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                let token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return false;
                }

                axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
                axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
                return true;
            }
        },
    });
</script>



