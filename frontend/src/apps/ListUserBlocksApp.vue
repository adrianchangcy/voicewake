<template>
    <div>
        <!--only update blocked_users once from [] to [...], not twice, to prevent bugs-->
        <DynamicScroller
            v-if="blocked_users.length > 0"
            :items="blocked_users"
            :min-item-size="2"
            :page-mode="true"
            :buffer="dynamic_scroller_buffer"
            keyField="scroller_id"
            class="scroller"
        >
            <template v-slot="{ item, index, active }">
                <DynamicScrollerItem
                    :item="item"
                    :index="index"
                    :active="active"
                >
                    <!--events-->
                    <!--DynamicScrollerItem has weird right side overflow clip-->
                    <!--px-1 is used to fix it, so other outer elements will require px-1 too-->
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
                                <span class="text-base font-normal text-ellipsis overflow-hidden">{{ item.username }}</span>
                            </VActionText>
                        
                            <!--block/unblock-->
                            <div class="w-fit flex-shrink-0">
                                <VActionBorder
                                    @click="postUserBlocks(index)"
                                    prop-element-size="s"
                                    prop-font-size="s"
                                    prop-element="button"
                                    :prop-is-enabled="!isProcessing(index)"
                                    :prop-is-icon-only="isProcessing(index) || item.is_blocked"
                                    type="button"
                                    :class="[
                                        item.is_blocked ? 'w-fit' : 'w-[7rem]',
                                        ''
                                    ]"
                                >
                                    <div
                                        v-show="isProcessing(index)"
                                        class="px-6 mx-auto"
                                    >
                                        <VLoading prop-element-size="s"/>
                                    </div>
                                    <span v-show="!isProcessing(index) && item.is_blocked" class="px-6 mx-auto flex items-center text-center">
                                        <FontAwesomeIcon icon="fas fa-xmark" class="mx-auto text-xl"/>
                                        <span class="sr-only">Unblock</span>
                                    </span>
                                    <span v-show="!isProcessing(index) && !item.is_blocked" class="mx-auto flex items-center text-center">
                                        <span class="pl-1">Block</span>
                                    </span>
                                </VActionBorder>
                            </div>
                        </div>
                    </div>
                </DynamicScrollerItem>
            </template>
        </DynamicScroller>

        <!--px-1 to match scroller-->
        <div
            v-show="canShowSkeleton"
            class="flex flex-col gap-2 px-1"
        >
            <div class="w-full h-14 rounded-lg skeleton"></div>
            <div class="w-full h-14 rounded-lg skeleton"></div>
            <div class="w-full h-14 rounded-lg skeleton"></div>
            <div class="w-full h-14 rounded-lg skeleton"></div>
        </div>

        <TransitionFade>
            <VDialogPlain
                v-if="canShowEmptyMessage"
                :prop-has-border="false"
                :prop-has-auto-space-logo="false"
                :prop-has-auto-space-title="false"
                :prop-has-auto-space-content="false"
                class="w-full px-1 pt-8"
            >
                <template #title>
                    <span>No users blocked.</span>
                </template>
            </VDialogPlain>
        </TransitionFade>
    </div>
</template>


<script setup lang="ts">
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VDialogPlain from '@/components/small/VDialogPlain.vue';
    import VActionText from '@/components/small/VActionText.vue';
    import VActionBorder from '@/components/small/VActionBorder.vue';
    import VLoading from '@/components/small/VLoading.vue';
    import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faCircle } from '@fortawesome/free-regular-svg-icons/faCircle';
    import { faUser } from '@fortawesome/free-solid-svg-icons/faUser';
    import { faXmark } from '@fortawesome/free-solid-svg-icons/faXmark';

    library.add(faCircle, faUser, faXmark);
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    // import { notify } from '@/wrappers/notify_wrapper';
    import { useUserBlocksStore } from '@/stores/UserBlocksStore';
    import { notify } from '@/wrappers/notify_wrapper';
    // import axios from 'axios';

    interface BlockedUsersTypes {
        scroller_id: number,
        username: string,
        is_blocked: boolean,
        is_processing: boolean,
    }

    //from this page, only unblocking matters
    export default defineComponent({
        name: 'ListUserBlocksApp',
        data(){
            return {
                user_blocks_store: useUserBlocksStore(),
                is_fetching: false,
                is_first_time_fetching: true,

                //corresponds to per-element in user_blocks_store.getBlockedUsernames
                //while never explicitly stated, demo at docs has shown that the virtual scroller plugin only works with [{},{}]
                //1D array will bug out
                blocked_users: [] as BlockedUsersTypes[],

                dynamic_scroller_buffer: 1000, //px, larger means rendered earlier, needed for proper tabbing
                window_resize_timeout: window.setTimeout(()=>{}, 0),
            };
        },
        computed: {
            canShowSkeleton() : boolean {

                return (
                    this.is_fetching === true &&
                    this.blocked_users.length === 0
                );
            },
            canShowEmptyMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.is_first_time_fetching === false &&
                    this.user_blocks_store.getBlockedUsernames.length === 0
                );
            },
        },
        methods: {
            initiateComponentFromStore() : void {

                //use setTimeout() in case it is so intensive that it blocks UI
                setTimeout(()=>{

                    //create copy, since the main store only updates via GET and does not allow changes from frontend
                    const blocked_usernames = [...this.user_blocks_store.getBlockedUsernames];

                    for(let x = 0; x < blocked_usernames.length; x++){

                        this.blocked_users.push({
                            scroller_id: x,
                            username: blocked_usernames[x],
                            is_blocked: true,
                            is_processing: false,
                        } as BlockedUsersTypes);
                    }
                }, 0);
            },
            getProfileURL(index:number) : string {

                return window.location.origin + '/user/' + this.blocked_users[index]['username'];
            },
            async getUserBlocks() : Promise<void> {

                if(this.is_first_time_fetching === false && this.is_fetching === true){

                    return;
                }

                this.is_first_time_fetching = false;
                this.is_fetching = true;

                await this.user_blocks_store.getUserBlocksAPI()
                .then(()=>{

                    this.initiateComponentFromStore();

                }).finally(()=>{

                    this.is_fetching = false;
                });
            },
            async postUserBlocks(index:number) : Promise<void>{

                //let row stay if unblock, so user can re-block if needed
                //also prevents the necessity of rediscovering index on update

                if(
                    index >= this.blocked_users.length ||
                    this.blocked_users[index]['is_processing'] === true
                ){

                    throw new Error('Out of range.');
                }

                const target_username = this.blocked_users[index]['username'];
                this.blocked_users[index]['is_processing'] = true;

                //rediscover index to avoid using old array context on new potentially-updated array context
                //use setTimeout to avoid blocking thread in case array is too huge

                await this.user_blocks_store.postUserBlocksAPI(target_username, !this.blocked_users[index]['is_blocked'])
                .then(()=>{

                    this.blocked_users[index]['is_blocked'] = !this.blocked_users[index]['is_blocked'];

                }).catch((error:any)=>{

                    let error_title = '';
                    let error_text = '';

                    if(this.blocked_users[index]['is_blocked'] === true){

                        //failed to unblock
                        error_title = 'Unblock failed';
                        error_text = error.response.data['message'];

                    }else{

                        //failed to block
                        error_title = 'Block failed';
                        error_text = error.response.data['message'];
                    }

                    notify({
                        'type': 'error',
                        'title': error_title,
                        'text': error_text
                    }, 4000);

                }).finally(()=>{

                    this.blocked_users[index]['is_processing'] = false;
                });
            },
            isProcessing(index:number) : boolean {

                return this.blocked_users[index]['is_processing'];
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