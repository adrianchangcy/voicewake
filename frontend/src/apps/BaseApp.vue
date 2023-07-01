<template>
    <NavBar
        :propIsLoggedIn="is_logged_in"
        :propUsername="username"
    />
</template>


<script setup lang="ts">
    import NavBar from '@/components/main/NavBar.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { getDataFromTemplate } from '@/helper_functions';

    export default defineComponent({
        name: 'BaseApp',
        data(){
            return {
                is_logged_in: false,
                username: "",
                must_set_username: false,
            };
        },
        beforeMount(){

            //is logged in
            this.is_logged_in = getDataFromTemplate("data-is-authenticated") as boolean;

            //username
            const username = getDataFromTemplate("data-username") as string|null;

            if(username !== null){

                this.username = username;
            }
        },
    });
</script>


