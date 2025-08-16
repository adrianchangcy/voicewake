<template>
    <div class="h-10 flex flex-row items-end pb-2 text-sm text-theme-black dark:text-dark-theme-white-2">
        <a
            :href="getUsernameURL"
            class="w-fit h-full flex items-end rounded-md transition-colors    action-text-hover active:bg-theme-gray-3 dark:active:bg-dark-theme-gray-3    focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline dark:focus-visible:outline-dark-theme-outline"
        >
            <div class="w-fit h-fit flex flex-row gap-2 overflow-hidden">
                <FontAwesomeIcon icon="fas fa-user" class="text-base"/>
                <span class="h-fit">{{ propUsername }}</span>
            </div>
        </a>
        <span v-if="propShowRepliedText" class="italic w-fit h-fit">
            &nbsp;replied
        </span>
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
                default: '',
            },
            propShowRepliedText: {
                type: Boolean,
                default: false,
            },
        },
        computed: {
            getUsernameURL() : string {

                return window.location.origin + '/user/' + this.propUsername;
            },
        },
    });
</script>