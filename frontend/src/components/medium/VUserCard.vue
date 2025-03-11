<template>
    <div>
        <div class="flex flex-col gap-2 px-2 py-6 pt-4 border-4 border-theme-black">

            <div class="flex flex-row items-center">
                <FontAwesomeIcon icon="fas fa-user" class="text-2xl pl-2 pr-4"/>
                <span class="text-2xl font-medium break-all">{{ username }}</span>
            </div>

            <div
                v-if="propHasDefaultActions"
                class="flex flex-row gap-1"
            >
                <VActionBorder
                    @click="copyUserURL()"
                    prop-element-size="s"
                    prop-font-size="s"
                    prop-element="button"
                    type="button"
                    class="w-[6rem]"
                >
                    <TransitionFade>
                        <span v-if="has_shared === false" class="mx-auto flex items-center text-center">
                            <FontAwesomeIcon icon="fas fa-share" class="text-base"/>
                            <span class="pl-1">Share</span>
                        </span>
                        <span v-else class="mx-auto flex items-center text-center">
                            <FontAwesomeIcon icon="fas fa-check" class="text-base"/>
                            <span class="pl-1">Copied</span>
                        </span>
                    </TransitionFade>
                </VActionBorder>

                <VActionBorder
                    v-if="canUseUserActions"
                    @click="handleBlock()"
                    prop-element-size="s"
                    prop-font-size="s"
                    prop-element="button"
                    :prop-is-enabled="!is_block_processing"
                    :prop-is-icon-only="is_block_processing"
                    type="button"
                    class="w-[7rem]"
                >
                    <div
                        v-if="is_block_processing"
                        class="mx-auto"
                    >
                        <VLoading prop-element-size="s"/>
                    </div>
                    <span v-else class="mx-auto flex items-center text-center">
                        <FontAwesomeIcon v-show="!is_blocked" icon="fas fa-ban" class="text-base"/>
                        <FontAwesomeIcon v-show="is_blocked" icon="fas fa-check" class="text-base"/>
                        <span v-show="!is_blocked" class="pl-1">Block</span>
                        <span v-show="is_blocked" class="pl-1">Blocked</span>
                    </span>
                </VActionBorder>

                <VActionBorder
                    v-if="canUseUserActions"
                    @click="handleFollow()"
                    prop-element-size="s"
                    prop-font-size="s"
                    prop-element="button"
                    :prop-is-enabled="!is_follow_processing"
                    :prop-is-icon-only="is_follow_processing"
                    type="button"
                    class="w-[7rem]"
                >
                    <div
                        v-if="is_follow_processing"
                        class="mx-auto"
                    >
                        <VLoading prop-element-size="s"/>
                    </div>
                    <span v-else class="mx-auto flex items-center text-center">
                        <FontAwesomeIcon v-show="!is_following" icon="far fa-star" class="text-base"/>
                        <FontAwesomeIcon v-show="is_following" icon="fas fa-check" class="text-base"/>
                        <span v-show="!is_following" class="pl-1">Follow</span>
                        <span v-show="is_following" class="pl-1">Following</span>
                    </span>
                </VActionBorder>
            </div>

            <div v-else class="text-xl font-medium pl-2">
                <slot></slot>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    import VLoading from '../small/VLoading.vue';
    import VActionBorder from '../small/VActionBorder.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faCircle } from '@fortawesome/free-regular-svg-icons/faCircle';
    import { faUser } from '@fortawesome/free-solid-svg-icons/faUser';
    import { faShare } from '@fortawesome/free-solid-svg-icons/faShare';
    import { faCheck } from '@fortawesome/free-solid-svg-icons/faCheck';
    import { faBan } from '@fortawesome/free-solid-svg-icons/faBan';
    import { faStar } from '@fortawesome/free-regular-svg-icons/faStar';

    library.add(faCircle, faUser, faShare, faCheck, faBan, faStar);
</script>


<script lang="ts">
    import { PropType, defineComponent } from 'vue';
    import { notify } from '@/wrappers/notify_wrapper';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    import { useUserBlocksStore } from '@/stores/UserBlocksStore';
    import { useUserFollowsStore } from '@/stores/UserFollowsStore';
    // import anime from 'animejs';

    export default defineComponent({
        data(){
            return {
                pop_up_manager_store: usePopUpManagerStore(),
                user_blocks_store: useUserBlocksStore(),
                user_follows_store: useUserFollowsStore(),

                username: '',
                has_shared: false,
                has_shared_timeout: null as number|null,

                is_blocked: false,
                is_block_processing: false,

                is_following: false,
                is_follow_processing: false,

                is_own_user_page: false,
            };
        },
        props: {
            propPageContext: {
                type:String as PropType<"home"|"user_profile"|"user_likes_dislikes">,
                default: "home",
            },
            propHasDefaultActions: {
                type: Boolean,
                default: true,
            },
        },
        computed: {
            canUseUserActions() : boolean {

                return (
                    this.pop_up_manager_store.isLoggedIn === true &&
                    this.is_own_user_page === false
                );
            },
        },
        methods: {
            async handleBlock() : Promise<void> {

                if(this.is_block_processing === true){

                    return;
                }

                this.is_block_processing = true;

                await this.user_blocks_store.postUserBlocksAPI(this.username, !this.is_blocked)
                .then(()=>{

                    this.is_blocked = !this.is_blocked;

                }).finally(()=>{

                    this.is_block_processing = false;
                });
            },
            async handleFollow() : Promise<void> {

                if(this.is_follow_processing === true){

                    return;
                }

                this.is_follow_processing = true;

                await this.user_follows_store.postUserFollowsAPI(this.username, !this.is_following)
                .then(()=>{

                    this.is_following = !this.is_following;

                }).finally(()=>{

                    this.is_follow_processing = false;
                });
            },
            copyUserURL() : void {

                if(this.has_shared_timeout !== null){

                    return;
                }

                const url = window.origin + "/user/" + this.username;
                navigator.clipboard.writeText(url);

                notify({
                    type: 'ok',
                    title: 'Link copied',
                    text: '',
                }, 2000);

                this.has_shared = true;

                this.has_shared_timeout = window.setTimeout(()=>{
                    this.has_shared = false;
                    this.has_shared_timeout !== null ? window.clearTimeout(this.has_shared_timeout) : null;
                    this.has_shared_timeout = null;
                }, 2000);
            },
        },
        beforeMount(){

            if(this.propPageContext === 'user_profile'){

                const container = (document.getElementById('data-container-get-user-profile') as HTMLElement);
                this.username = (container.getAttribute('data-username') as string);
                this.is_own_user_page = JSON.parse(container.getAttribute('data-is-own-page') as string);
                this.is_blocked = JSON.parse(container.getAttribute('data-is-blocked') as string);
                this.is_following = JSON.parse(container.getAttribute('data-is-following') as string);

            }else if(this.propPageContext === 'user_likes_dislikes'){

                const container = (document.getElementById('data-container-list-user-likes-dislikes') as HTMLElement);
                this.username = (container.getAttribute('data-username') as string);
                this.is_own_user_page = JSON.parse(container.getAttribute('data-is-own-page') as string);
            }
        }
    });
</script>