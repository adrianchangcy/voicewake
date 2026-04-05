<template>
    <VNavBar
        :propIsLoggedIn="is_logged_in"
        :propUsername="username"
    />

    <!--extra popups can belong here-->
    <div class="w-full h-0 relative">
        <div
            v-if="pop_up_manager_store.isCancelConfirmOpen && pop_up_manager_store.getCurrentPopupKwargs !== null"
            class="absolute flex flex-row w-full h-[calc(100vh-4.5rem)] bg-theme-light/90 dark:bg-theme-dark/90"
        >
            <div
                class="w-3/4 sm:w-2/4 md:w-1/4 xl:w-3/12 2xl:w-2/12 max-h-[90%] min-h-fit m-auto"
            >
                <VPopupCancelConfirm
                    :propTitle="pop_up_manager_store.getCurrentPopupKwargs.prop_title"
                    :propDescription="pop_up_manager_store.getCurrentPopupKwargs.prop_description"
                    :propCancellationTerm="pop_up_manager_store.getCurrentPopupKwargs.prop_cancellation_term"
                    :propCancellationCallback="pop_up_manager_store.getCurrentPopupKwargs.prop_cancellation_callback"
                    :propConfirmationTerm="pop_up_manager_store.getCurrentPopupKwargs.prop_confirmation_term"
                    :propConfirmationCallback="pop_up_manager_store.getCurrentPopupKwargs.prop_confirmation_callback"
                    @force-close="pop_up_manager_store.closeCancelConfirmPopup()"
                />
            </div>
        </div>
    </div>

    <!--toasts-->
    <!--if pop-ups clash with toasts, do v-if here-->
    <div
        class="w-0 h-0"
    >
        <VNotiwind/>
        <VAudioClipProcessings/>
    </div>
</template>


<script setup lang="ts">
    import VNotiwind from '@/components/medium/VNotiwind.vue';
    import VAudioClipProcessings from '@/components/medium/VAudioClipProcessings.vue';
    import VNavBar from '@/components/main/VNavBar.vue';
    import VPopupCancelConfirm from '@/components/medium/VPopupCancelConfirm.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { usePageRefreshTriggerStore } from '@/stores/PageRefreshTriggerStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    import { useRedrawCanvasesStore } from '@/stores/RedrawCanvasesStore';
    import { notify } from '@/wrappers/notify_wrapper';
    import { axiosCSRFSetup, isLoggedIn, getUsername } from '@/helper_functions';

    export default defineComponent({
        name: 'BaseApp',
        data(){
            return {
                page_refresh_trigger_store: usePageRefreshTriggerStore(),
                pop_up_manager_store: usePopUpManagerStore(),
                redraw_canvases_store: useRedrawCanvasesStore(),

                is_logged_in: false,
                username: "",
            };
        },
        computed: {
        },
        methods: {
            checkHasCookiesConsent() : void {

                //currently not used
                //only need consent if collecting user data

                if(this.is_logged_in === false || localStorage.getItem('user_consents_to_cookies') !== null){

                    return;
                }

                notify({
                    type: 'generic',
                    title: 'Cookies Consent',
                    text: 'We use cookies so you can stay logged in.',
                    icon: {'font_awesome': 'fas fa-cookie-bite'},
                    actions: [{
                        type: 'button',
                        style: 'primary',
                        text: 'Accept',
                        callback: this.setCookiesConsent,
                    }]
                }, -1);
            },
            setCookiesConsent() : void {

                localStorage.setItem('user_consents_to_cookies', JSON.stringify(true));
            },
            closeAllPopupsOnEsc(event:KeyboardEvent) : void {

                if(event.key === 'Escape'){

                    this.pop_up_manager_store.closeAllPopups();
                }
            },
        },
        beforeMount(){

            axiosCSRFSetup();

            //is logged in
            this.is_logged_in = isLoggedIn();

            //username
            this.username = getUsername();

            //refresh all tabs when necessary
            //provided that every tab has BaseApp.vue
            this.page_refresh_trigger_store.$subscribe(()=>{

                this.page_refresh_trigger_store.resetRefreshContext();

                window.location.replace(window.location.href);
            });

            //allow use of ESC key to close popups
            window.addEventListener('keydown', this.closeAllPopupsOnEsc);
            window.addEventListener('resize', this.redraw_canvases_store.redrawAllAudioVolumePeakCanvases);

        },
        beforeUnmount(){

            window.removeEventListener('keydown', this.closeAllPopupsOnEsc);
            window.removeEventListener('resize', this.redraw_canvases_store.redrawAllAudioVolumePeakCanvases);
        }
    });
</script>


