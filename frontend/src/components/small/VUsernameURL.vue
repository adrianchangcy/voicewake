<template>
    <div>
        <a
            :href="user_url"
            class="w-fit h-fit overflow-hidden flex flex-row items-center gap-2 text-theme-black text-sm shade-text-when-hover transition-colors    focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-1 focus-visible:outline-theme-outline"
        >
            <i class="h-fit fas fa-user" aria-hidden="true"></i>
            <span class="h-fit break-all">{{ propUsername }}</span>
        </a>
    </div>
</template>


<script setup lang="ts">
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
                user_url: '',
            };
        },
        props: {
            propUsername: {
                type: String,
                default: ''
            },
        },
        beforeMount(){

            this.user_url = window.location.origin + '/user/' + this.propUsername;
        }
    });
</script>