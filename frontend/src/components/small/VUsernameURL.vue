<template>
    <div>
        <a
            :href="getUsernameURL"
            class="w-fit h-10 flex text-theme-black text-sm rounded-md transition-colors    action-text-hover active:bg-theme-gray-3    focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline"
        >
            <div class="w-fit h-fit self-end flex flex-row items-center gap-2 overflow-hidden pb-2">
                <FontAwesomeIcon icon="fas fa-user" class="text-base"/>
                <span class="h-fit">{{ propUsername }}</span>
            </div>
        </a>
    </div>
</template>


<script setup lang="ts">
    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faUser } from '@fortawesome/free-solid-svg-icons/faUser';

    library.add(faUser);
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        props: {
            propUsername: {
                type: String,
                default: ''
            },
        },
        computed: {
            getUsernameURL() : string {

                return window.location.origin + '/user/' + this.propUsername;
            },
        },
    });
</script>