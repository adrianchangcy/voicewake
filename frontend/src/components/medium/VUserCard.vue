<template>
    <div>
        <div class="flex flex-col p-4 border-4 border-theme-black">

            <div class="flex flex-row items-center">
                <!--username-->
                <div class="w-full flex flex-row items-center gap-2">
                    <FontAwesomeIcon icon="fas fa-user" class="text-2xl"/>
                    <span class="text-2xl font-medium break-all">{{ username }}</span>
                </div>
                <!--opener for more options-->
                <div
                    ref="open_close_user_card_options_menu_button"
                    class="items-end pl-2"
                >
                    <VActionBorder
                        v-if="canUseUserActions"
                        :class="[
                            is_user_card_options_menu_open ? 'border-2 border-theme-black dark:border-dark-theme-white-2' : 'border-theme-gray-form-field dark:border-dark-theme-gray-form-field shade-border-when-hover',
                            'w-10 flex flex-row focus-visible:-outline-offset-2'
                        ]"
                        @click="toggleUserCardOptionsMenu"
                        prop-element-size="s"
                        prop-font-size="s"
                        prop-element="button"
                        :prop-is-enabled="true"
                        :prop-is-icon-only="true"
                        type="button"
                    >
                        <span class="mx-auto flex items-center text-center">
                            <FontAwesomeIcon icon="fas fa-ellipsis-vertical" class="text-base"/>
                            <span class="sr-only">More options</span>
                        </span>
                    </VActionBorder>
                </div>
            </div>

            <!--more options menu-->
            <div class="h-0 relative">
                <!--arrow-->
                <div
                    v-show="is_user_card_options_menu_open"
                    class="z-30 w-2 h-2 absolute top-1 right-4 m-auto bg-theme-light dark:bg-theme-dark border-l-2 border-t-2 border-theme-black dark:border-dark-theme-white-2 rotate-45"
                ></div>
                <!--more options-->
                <!--for child buttons, use click.stop to avoid closing on click-->
                <div
                    v-show="is_user_card_options_menu_open"
                    v-click-outside="{
                        bool_status_variable_or_callback: 'is_user_card_options_menu_open',
                        refs_to_exclude: ['open_close_user_card_options_menu_button']
                    }"
                    class="absolute z-20 top-2 right-0 w-[50%] rounded-lg p-4 border-2 border-theme-black dark:border-dark-theme-white-2 bg-theme-light dark:bg-theme-dark"
                >
                    <!--block-->
                    <VActionText
                        ref="user_card_options_menu_option_0"
                        @click.stop="handleBlock()"
                        prop-element-size="s"
                        prop-font-size="s"
                        prop-element="button"
                        :prop-is-enabled="!is_block_processing"
                        :prop-is-icon-only="is_block_processing"
                        type="button"
                        class="w-full"
                    >
                        <div v-show="is_block_processing" class="w-full h-full flex items-center">
                            <div class="mx-auto">
                                <VLoading prop-element-size="s"/>
                            </div>
                        </div>
                        <div v-show="!is_block_processing" class="w-full h-full flex items-center">
                            <div class="mx-auto">
                                <FontAwesomeIcon v-show="!is_blocked" icon="fas fa-ban" class="text-base"/>
                                <FontAwesomeIcon v-show="is_blocked" icon="fas fa-check" class="text-base"/>
                                <span v-show="!is_blocked" class="pl-2">Block</span>
                                <span v-show="is_blocked" class="pl-2">Blocked</span>
                            </div>
                        </div>
                    </VActionText>
                </div>
            </div>

            <div
                v-if="propHasDefaultActions"
                class="pt-2 grid grid-cols-2 gap-1"
            >
                <VActionBorder
                    @click="copyUserURL()"
                    prop-element-size="s"
                    prop-font-size="s"
                    prop-element="button"
                    type="button"
                    class="col-span-1"
                >
                    <TransitionGroupFade>
                        <div v-show="!has_shared" class="w-full h-full flex items-center">
                            <div class="mx-auto">
                                <FontAwesomeIcon icon="fas fa-share" class="text-base"/>
                                <span class="pl-2">Share</span>
                            </div>
                        </div>
                        <div v-show="has_shared" class="w-full h-full flex items-center">
                            <div class="mx-auto">
                                <FontAwesomeIcon icon="fas fa-check" class="text-base"/>
                                <span class="pl-2">Copied</span>
                            </div>
                        </div>
                    </TransitionGroupFade>
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
                    class="col-span-1"
                >
                    <div v-show="is_follow_processing" class="w-full h-full flex items-center">
                        <div class="mx-auto">
                            <VLoading prop-element-size="s"/>
                        </div>
                    </div>
                    <div v-show="!is_follow_processing" class="w-full h-full flex items-center">
                        <div class="mx-auto">
                            <FontAwesomeIcon v-show="!is_following" icon="fas fa-star" class="text-base"/>
                            <FontAwesomeIcon v-show="is_following" icon="fas fa-check" class="text-base"/>
                            <span v-show="!is_following" class="pl-2">Follow</span>
                            <span v-show="is_following" class="pl-2">Following</span>
                        </div>
                    </div>
                </VActionBorder>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    import VLoading from '../small/VLoading.vue';
    import VActionBorder from '../small/VActionBorder.vue';
    import VActionText from '../small/VActionText.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faCircle } from '@fortawesome/free-regular-svg-icons/faCircle';
    import { faUser } from '@fortawesome/free-solid-svg-icons/faUser';
    import { faShare } from '@fortawesome/free-solid-svg-icons/faShare';
    import { faCheck } from '@fortawesome/free-solid-svg-icons/faCheck';
    import { faBan } from '@fortawesome/free-solid-svg-icons/faBan';
    import { faStar } from '@fortawesome/free-solid-svg-icons/faStar';
    import { faEllipsisVertical } from '@fortawesome/free-solid-svg-icons/faEllipsisVertical';

    library.add(faCircle, faUser, faShare, faCheck, faBan, faStar, faEllipsisVertical);
</script>


<script lang="ts">
    import { PropType, defineComponent } from 'vue';
    import { notify } from '@/wrappers/notify_wrapper';
    import { useUserBlocksStore } from '@/stores/UserBlocksStore';
    import { useUserFollowsStore } from '@/stores/UserFollowsStore';
    import { isLoggedIn } from '@/helper_functions';
    // import anime from 'animejs';

    export default defineComponent({
        data(){
            return {
                user_blocks_store: useUserBlocksStore(),
                user_follows_store: useUserFollowsStore(),

                is_logged_in: false,
                username: '',
                has_shared: false,
                has_shared_timeout: null as number|null,

                is_user_card_options_menu_open: false,

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
                    this.is_logged_in === true &&
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
            toggleUserCardOptionsMenu(){

                this.is_user_card_options_menu_open = !this.is_user_card_options_menu_open;
            },
        },
        beforeMount(){

            this.is_logged_in = isLoggedIn();

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