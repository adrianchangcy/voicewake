<template>
    <div>
        <DynamicScroller
            v-show="user_blocks.length > 0"
            :items="user_blocks"
            :min-item-size="1"
            :buffer="dynamic_scroller_buffer"
            :page-mode="true"
            key-field="scroller_index_id"
            class="scroller"
        >

            <template #default="{ item, index, active }">

                <!--events-->
                <!--DynamicScrollerItem has weird right side overflow clip-->
                <!--px-1 is used to fix it, so other outer elements will require px-1 too-->
                <DynamicScrollerItem
                    :item="item"
                    :index="index"
                    :active="active"
                >
                    <div class="px-1 pb-2">
                        <div class="w-full flex flex-row items-center p-2 gap-4 border border-theme-gray-2 dark:border-dark-theme-gray-2 active:bg-theme-gray-3 dark:active:bg-dark-theme-gray-3 transition-colors shade-border-when-hover rounded-lg">
                            <!--user-->
                            <VActionText
                                prop-element="a"
                                :href="getProfileURL(index)"
                                prop-element-size="s"
                                prop-font-size="s"
                                class="min-w-0 flex-grow"
                            >
                                <FontAwesomeIcon icon="fas fa-user" class="text-base pl-2 pr-4"/>
                                <span class="text-base font-normal text-ellipsis overflow-hidden">{{ item.blocked_user.username }}</span>
                            </VActionText>
                        
                            <!--block/unblock-->
                            <div class="w-fit flex-shrink-0">
                                <VActionBorder
                                    @click="handleBlock(index)"
                                    prop-element-size="s"
                                    prop-font-size="s"
                                    prop-element="button"
                                    :prop-is-enabled="!isBlocking(index)"
                                    :prop-is-icon-only="isBlocking(index)"
                                    type="button"
                                    class="w-[7rem]"
                                >
                                    <div
                                        v-show="isBlocking(index)"
                                        class="mx-auto"
                                    >
                                        <VLoading prop-element-size="s"/>
                                    </div>
                                    <span v-show="!isBlocking(index)" class="mx-auto flex items-center text-center">
                                        <FontAwesomeIcon v-show="!item.is_blocked" icon="fas fa-ban" class="text-base"/>
                                        <FontAwesomeIcon v-show="item.is_blocked" icon="far fa-circle" class="text-base"/>
                                        <span v-show="!item.is_blocked" class="pl-1">Block</span>
                                        <span v-show="item.is_blocked" class="pl-1">Unblock</span>
                                    </span>
                                </VActionBorder>
                            </div>
                        </div>
                    </div>
                </DynamicScrollerItem>
            </template>
        </DynamicScroller>

        <div
            v-show="is_fetching"
            class="flex flex-col gap-2 px-1"
        >
            <div class="w-full h-14 rounded-lg skeleton"></div>
            <div class="w-full h-14 rounded-lg skeleton"></div>
        </div>

        <TransitionFade>
            <VDialogPlain
                v-if="canShowEmptyMessage || canShowEndOfPageMessage"
                :prop-has-border="false"
                :prop-has-auto-space-logo="false"
                :prop-has-auto-space-title="false"
                :prop-has-auto-space-content="false"
                class="w-full px-1 pt-8"
            >
                <template #title>
                    <span v-show="canShowEmptyMessage">No users blocked.</span>
                    <span v-show="canShowEndOfPageMessage">You've reached the end of this page.</span>
                </template>
            </VDialogPlain>
        </TransitionFade>

        <div id="load-more-user-blocks-observer-target"></div>
    </div>
</template>


<script setup lang="ts">
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VDialogPlain from '../components/small/VDialogPlain.vue';
    import VActionText from '../components/small/VActionText.vue';
    import VActionBorder from '../components/small/VActionBorder.vue';
    import VLoading from '../components/small/VLoading.vue';
    import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faCircle } from '@fortawesome/free-regular-svg-icons/faCircle';
    import { faUser } from '@fortawesome/free-solid-svg-icons/faUser';
    import { faBan } from '@fortawesome/free-solid-svg-icons/faBan';

    library.add(faCircle, faUser, faBan);
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from '@/wrappers/notify_wrapper';
    const axios = require('axios');

    interface UserBlocksTypes {
        blocked_user: {
            username: string,
        },
        is_blocked: boolean
    }

    interface ScrollableUserBlocksTypes extends UserBlocksTypes {
        scroller_index_id: number,
    }

    export default defineComponent({
        name: 'ListUserBlocksApp',
        data(){
            return {
                user_blocks: [] as ScrollableUserBlocksTypes[],
                is_blocking: false,
                is_blocking_index: null as number|null,

                dynamic_scroller_buffer: 1000, //px, larger means rendered earlier, needed for proper tabbing
                window_resize_timeout: window.setTimeout(()=>{}, 0),

                next_url: window.location.origin + '/api/users/blocks/list/next',
                back_url: window.location.origin + '/api/users/blocks/list/back',

                is_fetching: false,
                can_observer_fetch: false,
                has_no_user_blocks_left_to_fetch: false,
            };
        },
        computed: {
            canShowEmptyMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.user_blocks.length === 0 &&
                    this.has_no_user_blocks_left_to_fetch === true
                );
            },
            canShowEndOfPageMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.user_blocks.length > 0 &&
                    this.has_no_user_blocks_left_to_fetch === true
                );
            },
        },
        methods: {
            getProfileURL(index:number) : string {

                return window.location.origin + '/user/' + this.user_blocks[index].blocked_user.username;
            },
            isBlocking(index:number) : boolean {

                return this.is_blocking === true && this.is_blocking_index === index;
            },
            async handleBlock(user_block_index:number) : Promise<void> {

                if(this.is_blocking === true){

                    return;
                }

                this.is_blocking = true;
                this.is_blocking_index = user_block_index;

                const url = window.location.origin + '/api/users/blocks';

                let data = new FormData();
                data.append('username', this.user_blocks[user_block_index].blocked_user.username);
                data.append('to_block', JSON.stringify(!this.user_blocks[user_block_index].is_blocked));

                await axios.post(url, data)
                .then(()=>{

                    this.user_blocks[user_block_index].is_blocked = !this.user_blocks[user_block_index].is_blocked;

                }).catch(()=>{

                    const block_text = this.user_blocks[user_block_index].is_blocked === true ? 'unblock' : 'block';

                    notify({
                        type: 'error',
                        title: 'Error',
                        text: 'Unable to ' + block_text + ' that user at the moment.',
                        icon: {'font_awesome': 'fas fa-exclamation'},
                    }, 2000);

                }).finally(()=>{

                    this.is_blocking = false;
                    this.is_blocking_index = null;
                })
            },
            async getUserBlocks() : Promise<void> {

                if(this.is_fetching === true){

                    return;
                }

                this.is_fetching = true;
                this.can_observer_fetch = false;
                this.has_no_user_blocks_left_to_fetch = false;

                await axios.get(this.next_url)
                .then((result:any) => {

                    if(result.data['data'].length === 0){

                        this.has_no_user_blocks_left_to_fetch = true;
                        return;
                    }

                    result.data['data'].forEach((user_block:UserBlocksTypes)=>{

                        (user_block as ScrollableUserBlocksTypes).scroller_index_id = this.user_blocks.length;
                        this.user_blocks.push(user_block as ScrollableUserBlocksTypes);
                    });

                    this.next_url = result.data['next_url'];
                    this.back_url = result.data['back_url'];

                }).catch(() => {

                    notify({
                        type: 'error',
                        title: 'Error',
                        text: "Unable to get the list of users you've blocked.",
                        icon: {'font_awesome': 'fas fa-exclamation'},
                    }, 4000);

                }).finally(() => {

                    this.is_fetching = false;
                    this.can_observer_fetch = true;
                });
            },
            setUpObserver() : void {

                //set up observer for infinite scroll
                const observer_target = document.querySelector('#load-more-user-blocks-observer-target');

                const observer = new IntersectionObserver(()=>{

                    if(
                        this.can_observer_fetch === false ||
                        this.has_no_user_blocks_left_to_fetch === true
                    ){

                        return;
                    }

                    this.getUserBlocks();
                }, {
                    threshold: 1,
                });

                if(observer_target !== null){

                    observer.observe(observer_target);
                }
            },
            async handleWindowResize() : Promise<void> {

                //we do our best to cater to user's viewport height to ensure sufficient buffer size
                //else elements are late to render, causing tab focus and whitespace issues

                this.window_resize_timeout !== null ? clearTimeout(this.window_resize_timeout) : null;

                //run this delayed one next, in case immediate call had fired before dimension is fixed
                this.window_resize_timeout = window.setTimeout(async ()=>{
                    this.dynamic_scroller_buffer = window.innerHeight * 2;
                }, 200);
            },
        },
        beforeMount(){

            history.scrollRestoration = 'manual';

            this.getUserBlocks();
        },
        mounted(){

            this.setUpObserver();

            //reassign buffer size in case screen height > 1000px
            //better bigger than smaller
            this.dynamic_scroller_buffer = window.innerHeight * 2;

            window.addEventListener('resize', this.handleWindowResize);
        },
        beforeUnmount(){

            window.removeEventListener('resize', this.handleWindowResize);
        },
    });
</script>