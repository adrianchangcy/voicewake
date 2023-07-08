<template>
    <div
        v-show="propIsOpen"
        class="w-full h-fit flex flex-col gap-2 p-4 bg-theme-light"
    >
        <VPlayback
            ref="audio_playback"
            :propAudio="final_blob"
            :propAudioVolumePeaks="blob_volume_peaks"
            :propBucketQuantity="propBucketQuantity"
            :propIsRecording="is_recording"
            :propRecordingVisualiserVolume="recording_volume"
            :propRecordingVisualiserTimeInterval="time_interval"
            :propIsForRecording="true"
            :propIsOpen="propIsOpen"
            @isAnimePlaybackCompleted="handleIsAnimePlaybackCompleted($event)"
            class="z-10"
        />
        <VRecorder
            :propIsAnimePlaybackCompleted="is_anime_playback_completed"
            :propTimeInterval="time_interval"
            :propMaxDuration="propMaxDuration"
            :propIsOpen="propIsOpen"
            @newRecording="handleNewRecording($event)"
            @isRecording="handleIsRecording($event)"
            @isCancelled="handleIsCancelled()"
            @newRecordingVolume="handleNewRecordingVolume($event)"
        />
    </div>
</template>


<script setup lang="ts">
    import VRecorder from '/src/components/medium/VRecorder.vue';
    import VPlayback from '/src/components/medium/VPlayback.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data() {
            return {
                is_recording: false,
                recording_volume: 0,
                time_interval: 200, //milliseconds
                is_anime_playback_completed: false,
                
                final_blob: null as Blob | null,
                blob_volume_peaks: [] as Array<number>,
            };
        },
        props: {
            propIsOpen: {
                type: Boolean,
                default: false
            },
            propBucketQuantity: {
                type: Number,
                required: true
            },
            propMaxDuration: {
                type: Number,
                required: true,
            },
        },
        emits: ['newRecording'],
        mounted(){

        },
        computed: {

        },
        methods: {
            handleIsCancelled() : void {

                //basically briefly show "Cancelled"
                console.log('yowza');

            },
            async handleNewRecording(new_value:{'blob':Blob|null, 'blob_duration':number}) : Promise<void> {

                //get file volumes, then store file
                //no need to store null on error, we keep existing file
                const audio_context = new AudioContext();

                await (new_value['blob'] as Blob).arrayBuffer()
                    .then((buffer:ArrayBuffer) => audio_context.decodeAudioData(buffer))
                    .then((decoded_audio:AudioBuffer) => decoded_audio.getChannelData(0)) //only 1 channel as expected
                    .then((audio_data:Float32Array) => this.getFileVolumes(audio_data))
                    .then((volume_peaks) => {

                        this.final_blob = new_value['blob'];
                        this.blob_volume_peaks = volume_peaks;


                        this.$emit('newRecording', {
                            'blob' : new_value['blob'],
                            'blob_duration' : new_value['blob_duration'],
                            'blob_volume_peaks' : volume_peaks
                        });
                    })
                    .catch((error:any|Error) => {
                        console.log(error);
                    });
            },
            handleIsRecording(new_value:boolean) : void {
                this.is_recording = new_value;
            },
            handleNewRecordingVolume(new_value:number) : void {
                this.recording_volume = new_value;
            },
            handleIsAnimePlaybackCompleted(new_value:boolean) : void {
                this.is_anime_playback_completed = new_value;
            },
            getFileVolumes(audio_data:Float32Array) : number[] {

                let bucket_peaks = [];
                let bucket_threshold = Math.round(audio_data.length / this.propBucketQuantity);
                //-1 to adjust for for-loop and lets us run code on last sample of each bucket (avoids < _ -1)
                let bucket_threshold_count = bucket_threshold - 1;
                let bucket_max = 0;

                for(let x = 0; x < audio_data.length; x++){

                    //check if we are at last sample of current bucket
                    if(x === bucket_threshold_count){

                        //set 2 decimal places, i.e. 0.00
                        bucket_max = parseFloat(bucket_max.toFixed(2));

                        //store max peak
                        bucket_peaks.push(bucket_max);

                        //reset
                        bucket_max = 0;

                        //shift to next bucket
                        bucket_threshold_count += bucket_threshold;
                    }
                    
                    //evaluate max peak in current bucket
                    if(audio_data[x] > bucket_max){

                        bucket_max = audio_data[x];
                    }
                }

                //if file is too short or cannot be equally divided, fill up with 0 to meet propBucketQuantity target
                while(bucket_peaks.length < this.propBucketQuantity){

                    bucket_peaks.push(0);
                }

                //return highest peaks
                return bucket_peaks;

                //we don't calculate volume range because it is unnecessary
                //0.1-0.2 is not 55%-60% but 0%-100%
                //min and max range is also -1 to 1, so need extra 'if' statements
                //lastly, we expect -1 to 1, but at 0 audio, we get only -0.0001
            },
        },

    });

</script>