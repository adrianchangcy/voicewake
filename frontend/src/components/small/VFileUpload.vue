<template>


</template>


<script setup lang="ts">

</script>


<script>
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {

                final_file: null as File|null,
                max_audio_file_size_mb: 10,
                audio_file_extensions_allowed: ['mp3','webm'], //webm, even if video, is seamlessly handled by <audio>
            };
        },
        methods: {

            attachRecordedAudioToInput() : boolean {

                if(this.final_file === null){

                    alert('Could not attach your file for upload because the file is empty.');
                    return false;
                }
                    
                //create new container to replace <input type="file"> container later
                let container = new DataTransfer();

                //add
                container.items.add(this.final_file);

                //replace files of <input type="file"> with DataTransfer() files
                (this.$refs.audio_upload as any).files = container.files;

                return true;
            },
            checkUploadedFileSizeIsValid(file:File, max_size_mb:number) : boolean {

                //mks with File() and files uploaded through <input type="file">

                let file_size_mb = file.size / (1000 * 1000);   //** not supported in IE browser

                if(file_size_mb > max_size_mb){

                    return false;
                }

                return true;
            },
            checkUploadedFileTypeIsValid(file:File) : boolean {

                //handles names with no extension, and names that start with '.', while also being most performant

                let file_name =  file.name;
                let file_extension = (file_name.slice((file_name.lastIndexOf(".") - 1 >>> 0) + 2)).toLowerCase();

                if(!this.audio_file_extensions_allowed.includes(file_extension)){
                    
                    return false;
                }

                return true;
            },
            validateUploadedFile() : boolean {

                let input_audio_upload:any = this.$refs.audio_upload;

                if(input_audio_upload.files.length > 0){
                    
                    this.final_file = input_audio_upload.files.item(0);

                    //TS is unhappy without this line
                    if(this.final_file === null){ return false;}

                    //check file size
                    if(this.checkUploadedFileSizeIsValid(this.final_file, this.max_audio_file_size_mb) === false){

                        alert('Uploaded file has exceeded limit of '+this.max_audio_file_size_mb+'MB!');
                        input_audio_upload.value = null;
                        return false;
                    }

                    //check file format
                    if(this.checkUploadedFileTypeIsValid(this.final_file) === false){

                        let temp_string = '';

                        for(let x = 0; x < this.audio_file_extensions_allowed.length; x++){

                            temp_string += this.audio_file_extensions_allowed[x].toUpperCase();

                            if(x < this.audio_file_extensions_allowed.length - 1){

                                temp_string += ', ';
                            }
                        
                        }

                        alert('Uploaded file type is not supported. Please use one of the following: '+temp_string);
                        input_audio_upload.value = null;
                        return false;
                    }

                    //ok
                    alert('Success! Uploaded file meets requirements.');

                    //attach recorded audio to playback
                    // this.attachRecordedAudioToPlayback();

                }else{

                    return false;
                }

            return true;
            },
        }
    });
</script>