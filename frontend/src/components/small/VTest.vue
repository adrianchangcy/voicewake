<template>
    <div>
        <span>{{ ooga_count }}</span>
    </div>
</template>

<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
                ooga_count: 0,
                yolo_elements: [] as HTMLElement[],
            };
        },
        watch: {
            ooga_count(new_value){
                console.log('new ooga_count from VTest' + new_value.toString());
            },
        },
        methods: {
            addOogaCount(){
                this.ooga_count += 1;
            },
        },
        mounted(){

        },

    });
</script>