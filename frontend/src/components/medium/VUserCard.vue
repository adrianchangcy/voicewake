<template>
    <div>
        <div class="flex flex-col gap-2 px-2 py-6 pt-4 rounded-lg border-2 border-theme-black">

            <div class="flex flex-row items-center">
                <i class="fas fa-user text-2xl pl-2 pr-4" aria-hidden="true"></i>
                <span class="text-2xl font-medium break-all">{{ propUsername }}</span>
            </div>

            <div class="flex flex-row gap-1">
                <VActionSimplest
                    @click="copyUserURL()"
                    prop-element-size="s"
                    prop-font-size="s"
                    prop-element="button"
                    type="button"
                    class="w-[6rem]"
                >
                    <TransitionFade>
                        <span v-if="has_shared === false" class="mx-auto flex items-center text-center">
                            <i class="fas fa-share text-base" aria-hidden="true"></i>
                            <span class="pl-1">Share</span>
                        </span>
                        <span v-else class="mx-auto flex items-center text-center">
                            <i class="fas fa-check text-base" aria-hidden="true"></i>
                            <span class="pl-1">Copied</span>
                        </span>
                    </TransitionFade>
                </VActionSimplest>

                <VActionSimplest
                    v-if="canBlockUnblock"
                    @click="handleBlock()"
                    prop-element-size="s"
                    prop-font-size="s"
                    prop-element="button"
                    :prop-is-enabled="!is_blocking"
                    :prop-is-icon-only="is_blocking"
                    type="button"
                    class="w-[7rem]"
                >
                    <div
                        v-if="is_blocking"
                        class="mx-auto"
                    >
                        <VLoading prop-element-size="s"/>
                    </div>
                    <span v-else class="mx-auto flex items-center text-center">
                        <i v-show="!is_blocked" class="fas fa-ban text-base" aria-hidden="true"></i>
                        <i v-show="is_blocked" class="far fa-circle text-base" aria-hidden="true"></i>
                        <span v-show="!is_blocked" class="pl-1">Block</span>
                        <span v-show="is_blocked" class="pl-1">Unblock</span>
                    </span>
                </VActionSimplest>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    import VLoading from '../small/VLoading.vue';
    import VActionSimplest from '../small/VActionSimplest.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from 'notiwind';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    // import anime from 'animejs';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                pop_up_manager_store: usePopUpManagerStore(),
                is_own_profile: false,

                username: '',
                has_shared: false,
                has_shared_timeout: null as number|null,

                is_blocked: false,
                is_blocking: false,
            };
        },
        watch: {
        },
        props: {
            propUsername: {
                type: String,
                required: true
            },
        },
        computed: {
            canBlockUnblock() : boolean {

                return (
                    this.pop_up_manager_store.getIsLoggedIn === true &&
                    this.is_own_profile === false
                );
            },
        },
        methods: {
            async handleBlock() : Promise<void> {

                if(this.is_blocking === true){

                    return;
                }

                this.is_blocking = true;

                let data = new FormData();

                data.append('username', this.propUsername);
                data.append('to_block', JSON.stringify((!this.is_blocked)));

                await axios.post(window.location.origin + '/api/users/blocks', data)
                .then((results:any) => {

                    this.is_blocked = !this.is_blocked;

                    notify({
                        title: this.is_blocked === true ? 'Blocked user' : 'Unblocked user',
                        text: results.data['message'],
                        type: 'ok'
                    }, 2000);

                }).catch(()=>{

                    notify({
                        title: 'Unable to block',
                        text: 'Could not block this user. Try again later.',
                        type: 'error'
                    }, 4000);

                }).finally(()=>{

                    this.is_blocking = false;
                });
            },
            async copyUserURL() : Promise<void> {

                if(this.has_shared_timeout !== null){

                    return;
                }

                const url = window.origin + "/user/" + this.propUsername;
                navigator.clipboard.writeText(url);

                notify({
                    title: 'Link copied',
                    type: 'ok',
                }, 2000);

                this.has_shared = true;

                this.has_shared_timeout = window.setTimeout(()=>{
                    this.has_shared = false;
                    this.has_shared_timeout !== null ? window.clearTimeout(this.has_shared_timeout) : null;
                    this.has_shared_timeout = null;
                }, 2000);
            },
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                const token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return false;
                }

                axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
                axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
                return true;
            },
        },

        beforeMount(){

            const container = (document.getElementById('data-container-get-user-profile') as HTMLElement);
            this.username = (container.getAttribute('data-user-profile-username') as string);

            this.is_own_profile = JSON.parse(container.getAttribute('data-is-own-profile') as string);
            this.is_blocked = JSON.parse(container.getAttribute('data-is-blocked') as string);
        },
    });
</script>