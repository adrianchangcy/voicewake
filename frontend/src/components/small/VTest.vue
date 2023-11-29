<template>
    <div>
        <span>{{ ooga_count }}</span>
        <button type="button" @click="addOogaCount()" class="w-10 h-10"></button>
    </div>
</template>

<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
                ooga_count: 0,
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