<template>
    <!--
        we deal with csrf and form logic later
        we handle the design part of form first
        https://blog.xoxzo.com/2021/05/24/vue-with-django-rest-framework-api/
        https://docs.djangoproject.com/en/dev/howto/csrf/
    -->

    <div class="md:w-2/4 lg:w-3/6 xl:w-2/6 mx-auto h-fit bg-theme-light text-left text-lg pb-20">

        <div class="w-[90%] mx-auto">
            <VSectionTitle
                propTitle="Say"
                propTitleDescription="Fill in the fields below"
            />
        </div>



        <!--test-->
        <form
            spellcheck="false"
            class="w-[90%] mx-auto bg-theme-light flex flex-col gap-4 text-theme-black"
        >
            <!--title-->
            <VTextArea
            :propIsRequired="true"
            propElementId="event-name"
            propLabel="Short title"
            propPlaceholder=""
            :propMaxLength="40"
            :propHasTextCounter="true"
            :propHasStatusText="false"
            />

            <!--fields for open/close-->
            <div class="grid grid-cols-7 gap-2">

                <!--open/close VEventToneMenu-->
                <div class="col-span-2">
                    <VEventToneField
                        ref="event_tone_field"
                        propLabelText="Feeling"
                        :propEventToneChoice="event_tone_choice"
                        :propIsOpen="is_event_tone_menu_open"
                        @isOpen="handleIsEventToneMenuOpen($event)"
                    />
                </div>

                <!--open/close VRecorderMenu-->
                <div class="col-span-5">
                    <VRecorderField
                    :propIsOpen="is_recorder_menu_open"
                    :propBucketQuantity="bucket_quantity"
                    :propHasRecording="final_file !== null"
                    :propFileVolumes="file_volumes"
                    :propFileDuration="file_duration"
                    @isOpen="handleIsRecorderMenuOpen($event)"
                    />
                </div>
            </div>

            <!--menus-->
            <div class="w-full h-0 relative">

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
                <VEventToneMenu
                    :propIsOpen="is_event_tone_menu_open"
                    @eventToneSelected="handleEventToneSelected($event)"
                    class="absolute border-2 border-theme-black rounded-lg"
                />

                <!--recorder menu-->
                <VRecorderMenu
                    :propIsOpen="is_recorder_menu_open"
                    :propBucketQuantity="bucket_quantity"
                    :propMaxDuration="max_duration"
                    @newRecording="handleNewRecording($event)"
                    class="absolute border-2 border-theme-black rounded-lg"
                />
            </div>

            <!--submit-->
            <div class="w-[90%] mx-auto py-10">
                <VActionButtonBig class="mx-auto">
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

    export default defineComponent({
        data() {
            return {

                event_name: "",
                event_tone_id: null as string|null,
                event_message: "",

                is_event_tone_menu_open: false, //updates only from VEventToneField to VEventToneMenu, maybe use vuex
                event_tone_choice: null as EventToneTypes|null,

                is_recorder_menu_open: false,
                final_file: null as File|null,
                file_volumes: [] as number[],
                file_duration: 0,
                bucket_quantity: 20,
                // propMaxDuration: (1000 * 60 * 2) + 500,    //2m + 0.5s, as final_file is always +-0.1s away
                max_duration: 10000,    //2m + 0.5s, as final_file is always +-0.1s away
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

        },
        methods: {
            handleNewRecording(new_value:{'final_file':File, 'file_duration':number, 'file_volumes':number[]}) : void {

                this.final_file = new_value['final_file'];
                this.file_duration = new_value['file_duration'];
                this.file_volumes = new_value['file_volumes'];
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

            newEmojiChoice(new_value:string): void {
                this.event_tone_id = new_value;
            },

            handleSubmit(): void {
                console.log("y submit? lol");
            },
        },
    });
</script>



