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
            ooga_count(){
                console.log('new ooga_count from VTest: ' + this.ooga_count.toString());
            },
        },
        methods: {
            addOogaCount(new_value:number){
                this.ooga_count += new_value;
            },
            notExposed(){
                console.log('ooo');
            },
        },
        mounted(){
        },

    });
</script>