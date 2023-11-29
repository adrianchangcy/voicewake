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
                            :propAudioClip="item"
                            :propIsSelected="checkIsSelected(item.id)"
                            @isSelected="handleNewSelectedAudioClip($event)"
                        />
                    </div>
                </DynamicScrollerItem>
            </template>
        </DynamicScroller>

        <!--VAudioClipCard emits selection, which triggers :to, thus teleporting-->
        <!--presence of VAudioClipCard depends on VEventCard-->
        <div v-if="selected_audio_clip !== null">
            <Teleport :to="getVPlaybackTeleportId">
                <VPlayback
                    :propAudioClip="selected_audio_clip"
                    :propIsOpen="true"
                    :propAudioVolumePeaks="selected_audio_clip.audio_volume_peaks"
                    :propBucketQuantity="selected_audio_clip.audio_volume_peaks.length"
                    :propAutoPlayOnSourceChange="true"
                />
            </Teleport>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VAudioClipCard from '/src/components/medium/VAudioClipCard.vue';
    import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';
    import VPlayback from '@/components/medium/VPlayback.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import { useCurrentlyPlayingAudioClipStore } from '@/stores/CurrentlyPlayingAudioClipStore';

    export default defineComponent({
        data() {
            return {
                currently_playing_audio_clip_store: useCurrentlyPlayingAudioClipStore(),
                selected_audio_clip: null as AudioClipsTypes|null,

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
            getVPlaybackTeleportId() : string {

                if(this.selected_audio_clip === null){

                    return '';
                }

                return '#playback-teleport-audio-clip-id-' + this.selected_audio_clip.id;
            },
        },
        methods: {
            checkIsSelected(audio_clip_id:number) : boolean {

                return this.selected_audio_clip !== null && this.selected_audio_clip.id === audio_clip_id;
            },
            handleNewSelectedAudioClip(audio_clip:AudioClipsTypes) : void {

                this.currently_playing_audio_clip_store.$patch({
                    playing_audio_clip: audio_clip
                });
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
        mounted(){

            //listen to store
            this.currently_playing_audio_clip_store.$subscribe((mutation, state)=>{

                this.selected_audio_clip = state.playing_audio_clip as AudioClipsTypes|null;
            });

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