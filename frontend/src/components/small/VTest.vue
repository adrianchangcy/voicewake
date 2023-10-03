<template>
    <div></div>
</template>

<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
                ooga_count: 0,
            };
        },
        props: {
            propCallback: {
                type: Function,
                required: true
            }
        },
        watch: {
            ooga_count(new_value){
                console.log('new ooga_count from VTest' + new_value.toString());
            },
        },
        mounted(){

            this.propCallback();
        }
    });
</script>