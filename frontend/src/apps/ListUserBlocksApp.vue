<template>
    <div>

        <div class="flex flex-col gap-2">
            <div
                v-for="(user, index) in user_blocks" :key="index"
                class="w-full flex flex-row items-center p-2 gap-2 border border-theme-light-gray transition-colors shade-border-when-hover rounded-lg text-theme-black"
            >

                <!--user-->
                <VActionTextOnly
                    prop-element="a"
                    :href="getProfileURL(index)"
                    prop-element-size="s"
                    prop-font-size="s"
                    class="min-w-0 flex-grow"
                >
                    <i class="fas fa-user text-base pl-2 pr-4"></i>
                    <span class="text-base font-normal text-ellipsis overflow-hidden">{{ user.blocked_user.username }}</span>
                </VActionTextOnly>

                <!--block/unblock-->
                <div class="w-fit flex-shrink-0">

                    <TransitionFade>
                        <!--block-->
                        <VActionSimplest
                            v-if="!user.is_blocked"
                            @click="handleBlock(index)"
                            prop-element-size="s"
                            prop-font-size="s"
                            prop-element="button"
                            :prop-is-enabled="!isBlocking(index)"
                            :prop-is-icon-only="isBlocking(index)"
                            type="button"
                            class="w-[6rem]"
                        >
                            <div
                                v-if="isBlocking(index)"
                                class="mx-auto"
                            >
                                <VLoading prop-element-size="s"/>
                            </div>
                            <span v-else class="mx-auto flex items-center text-center">
                                <i class="fas fa-ban text-base" aria-hidden="true"></i>
                                <span class="pl-1">Block</span>
                            </span>
                        </VActionSimplest>

                        <!--unblock-->
                        <VActionTextOnly
                            v-else-if="user.is_blocked"
                            @click="handleBlock(index)"
                            :prop-is-enabled="!isBlocking(index)"
                            :prop-is-icon-only="true"
                            prop-element-size="s"
                            prop-font-size="s"
                            prop-element="button"
                            type="button"
                            class="w-10"
                        >
                            <VLoading
                                v-if="isBlocking(index)"
                                prop-element-size="s"
                                class="mx-auto"
                            />
                            <i v-else class="fas fa-square-minus text-2xl mx-auto" aria-hidden="true"></i>
                            <span class="sr-only">unblock</span>
                        </VActionTextOnly>
                    </TransitionFade>
                </div>
            </div>
        </div>

        <TransitionFade>
            <VDialogPlain
                v-show="canShowEmptyMessage || canShowEndOfPageMessage"
                :prop-has-border="false"
                :prop-has-auto-spacing="false"
                class="w-full py-8"
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
    import VDialogPlain from '@/components/small/VDialogPlain.vue';
    import VActionTextOnly from '@/components/small/VActionTextOnly.vue';
    import VActionSimplest from '@/components/small/VActionSimplest.vue';
    import VLoading from '@/components/small/VLoading.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from 'notiwind';
    const axios = require('axios');

    interface UserBlocksTypes {
        blocked_user: {
            username: string,
        },
        is_blocked: boolean
    }

    export default defineComponent({
        name: 'ListUserBlocksApp',
        data(){
            return {
                user_blocks: [] as UserBlocksTypes[],
                is_blocking: false,
                is_blocking_index: null as number|null,

                is_fetching: false,
                can_observer_fetch: false,
                has_no_user_blocks_left_to_fetch: false,
                current_page: 1,
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

                //your template must have {% csrf_token %}
                let token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return;
                }

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
                .then((results:any)=>{

                    this.user_blocks[user_block_index].is_blocked = !this.user_blocks[user_block_index].is_blocked;

                    notify({
                        title: this.user_blocks[user_block_index].is_blocked === true ? 'Blocked user' : 'Unblocked user',
                        text: results.data['message'],
                        type: 'ok'
                    }, 2000);

                }).catch(()=>{

                    notify({
                        title: 'Error',
                        text: 'Unable to get your list of blocked users.',
                        type: 'error'
                    }, 2000);

                }).finally(()=>{

                    this.is_blocking = false;
                    this.is_blocking_index = null;
                })
            },
            async getUserBlocks() : Promise<void> {

                this.is_fetching = true;
                this.can_observer_fetch = false;
                this.has_no_user_blocks_left_to_fetch = false;

                const url = window.location.origin + '/api/users/blocks/list/' + this.current_page.toString();

                await axios.get(url)
                .then((result:any) => {

                    console.log(result.data['data'].length);

                    result.data['data'].forEach((user_block:UserBlocksTypes)=>{

                        this.user_blocks.push(user_block);
                    });

                    if(result.data['data'].length > 0){

                        this.current_page += 1;

                    }else{

                        this.has_no_user_blocks_left_to_fetch = true;

                    }

                    this.can_observer_fetch = true;

                }).catch(() => {

                    notify({
                        title: 'Error',
                        text: "Unable to get the list of users you've blocked.",
                        type: 'error'
                    });

                }).finally(() => {

                    this.is_fetching = false;
                });
            },
            setUpObserver() : void {

                //set up observer for infinite scroll
                const observer_target = document.querySelector('#load-more-user-banned-audio-clips-observer-target');

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
        },
        beforeMount(){

            this.getUserBlocks();
        },
        mounted(){

            this.setUpObserver();
        }
    });
</script>