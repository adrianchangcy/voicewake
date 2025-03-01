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
                        <div class="w-full flex flex-row items-center p-2 gap-4 border border-theme-gray-2 dark:border-dark-theme-gray-2 transition-colors shade-border-when-hover rounded-lg">
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
    // import { notify } from '@/wrappers/notify_wrapper';
    import { useUserBlocksStore } from '@/stores/UserBlocksStore';
    // import axios from 'axios';


    //from this page, only unblocking matters
    export default defineComponent({
        name: 'ListUserBlocksApp',
        data(){
            return {
                user_blocks_store: useUserBlocksStore(),
                is_fetching: true,
                //corresponds to per-element in user_blocks_store.getBlockedUsernames
                //purposely reinitiate on new component render
                blocked_usernames: [] as string[],
                is_processing: [] as boolean[],
                api_post_calls_queue: [] as Promise<void>[],

                dynamic_scroller_buffer: 1000, //px, larger means rendered earlier, needed for proper tabbing
                window_resize_timeout: window.setTimeout(()=>{}, 0),
            };
        },
        computed: {
            canShowEmptyMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.user_blocks_store.getBlockedUsernames.length === 0
                );
            },
        },
        methods: {
            initiateComponentFromStore() : void {

                this.blocked_usernames = [...this.user_blocks_store.getBlockedUsernames];
                this.is_processing = [];

                for(let x = 0; x < this.user_blocks_store.getBlockedUsernames.length; x++){

                    this.is_processing.push(false);
                }
            },
            getProfileURL(index:number) : string {

                return window.location.origin + '/user/' + this.user_blocks_store.getBlockedUsernames[index];
            },
            async getUserBlocks() : Promise<void> {

                this.is_fetching = true;

                await this.user_blocks_store.getUserBlocksAPI()
                .then(()=>{

                    this.initiateComponentFromStore();

                }).finally(()=>{

                    this.is_fetching = false;
                });
            },
            async doUnblock(index:number) : Promise<void>{

                if(
                    index >= this.user_blocks_store.getBlockedUsernames.length ||
                    index >= this.api_post_calls_queue.length ||
                    this.is_processing[index] === true
                ){

                    throw new Error('Out of range.');
                }

                this.is_processing[index] = true;

                await this.user_blocks_store.postUserBlocksAPI(this.user_blocks_store.getBlockedUsernames[index], false)
                .then(()=>{

                    this.blocked_usernames.splice(index, 1);
                    this.is_processing.splice(index, 1);

                }).catch(()=>{

                    this.is_processing[index] = false;
                });
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

            this.initiateComponentFromStore();
        },
        mounted(){

            this.getUserBlocks();

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