<template>
    <div>

        <!--audio-clips-->
        <DynamicScroller
            v-show="propAudioClips.length > 0"
            :items="propAudioClips"
            :min-item-size="1"
            :buffer="dynamic_scroller_buffer"
            :page-mode="true"
            key-field="scroller_index_id"
            class="scroller"
        >

            <template #default="{ item, index, active }">

                <!--events-->
                <!--DynamicScrollerItem has weird right side overflow clip-->
                <!--px-1 is used to fix it, so other outer elements will require px-1 too-->
                <DynamicScrollerItem
                    :item="item"
                    :index="index"
                    :active="active"
                >
                    <div class="px-1 pb-4">
                        <VAudioClipCard
                            :prop-audio-clip="item"
                            :prop-selected-audio-clip="vplayback_store.getPlayingAudioClip"
                            @selectedAudioClip="vplayback_store.updatePlayingAudioClip($event)"
                            @newVPlaybackTeleportId="handleNewVPlaybackTeleportId($event)"
                        />
                    </div>
                </DynamicScrollerItem>
            </template>
        </DynamicScroller>

        <Teleport
            v-if="teleport_id !== ''"
            :to="teleport_id"
        >
            <VPlayback
                :prop-audio-clip="vplayback_store.getPlayingAudioClip"
                :prop-is-open="true"
                :prop-audio-volume-peaks="getSelectedAudioClipAudioVolumePeaks"
                :prop-bucket-quantity="20"
            />
        </Teleport>
    </div>
</template>

<script setup lang="ts">
    import VAudioClipCard from '../medium/VAudioClipCard.vue';
    import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';
    import VPlayback from '../medium/VPlayback.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';

    export default defineComponent({
        data() {
            return {
                vplayback_store: useVPlaybackStore(),
                teleport_id: '',

                window_resize_timeout: window.setTimeout(()=>{}, 0),
                dynamic_scroller_buffer: 1000, //px, larger means rendered earlier, needed for proper tabbing
            };
        },
        props: {
            propAudioClips: {
                type: Object as PropType<AudioClipsTypes[]>,
                required: true,
            },
            propShowTitle: {
                type: Boolean,
                default: true
            },
        },
        computed: {
            getSelectedAudioClipAudioVolumePeaks() : number[] {

                if(this.vplayback_store.getPlayingAudioClip === null){

                    return [];
                }

                return this.vplayback_store.getPlayingAudioClip.audio_volume_peaks;
            },
        },
        methods: {
            async handleNewVPlaybackTeleportId(teleport_id:string) : Promise<void> {

                this.teleport_id = teleport_id;
            },
            async handleWindowResize() : Promise<void> {

                //we do our best to cater to user's viewport height to ensure sufficient buffer size
                //else elements are late to render, causing tab focus and whitespace issues

                this.window_resize_timeout !== null ? clearTimeout(this.window_resize_timeout) : null;

                //run this delayed one next, in case immediate call had fired before dimension is fixed
                this.window_resize_timeout = window.setTimeout(async ()=>{
                    this.dynamic_scroller_buffer = window.innerHeight * 2;
                }, 200);
            },
        },
        beforeMount(){

            this.vplayback_store.autoplayOnChange(true);
        },
        mounted(){

            //reassign buffer size in case screen height > 1000px
            //better bigger than smaller
            this.dynamic_scroller_buffer = window.innerHeight * 2;

            window.addEventListener('resize', this.handleWindowResize);
        },
        beforeUnmount(){

            window.removeEventListener('resize', this.handleWindowResize);
        },
    });
</script>