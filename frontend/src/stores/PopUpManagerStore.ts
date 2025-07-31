import { defineStore } from 'pinia';



type PopupOptions =
    | {
        context: ""|"nav_menu"|"login_required"|"log_in"|"sign_up",
        kwargs: null,
    } | {
        context: "cancel_confirm",
        kwargs: {
            prop_title: string,
            prop_description: string,
            prop_cancellation_term: string,
            prop_cancellation_callback: Function,
            prop_confirmation_term: string,
            prop_confirmation_callback: Function,
        }
    };


//helps us manage pop-ups
//currently using redundant way of ensuring other pop-ups are closed when one opens
//still manageable because we have limited pop-ups
export const usePopUpManagerStore = defineStore('pop_up_manager', {
    state: ()=>({
        current_popup_option: {context: '', kwargs: null} as PopupOptions,
    }),
    getters: {
        getPopupOptionForReset: ()=>{
            return {context: '', kwargs: null} as PopupOptions;
        },
        isNavMenuOpen: (state)=>{
            return state.current_popup_option.context === 'nav_menu';
        },
        isLoginRequiredOpen: (state)=>{
            return state.current_popup_option.context === 'login_required';
        },
        isLogInOpen: (state)=>{
            return state.current_popup_option.context === 'log_in';
        },
        isSignUpOpen: (state)=>{
            return state.current_popup_option.context === 'sign_up';
        },
        isCancelConfirmOpen: (state)=>{
            return state.current_popup_option.context === 'cancel_confirm';
        },
        getCurrentPopupContext: (state)=>{
            return state.current_popup_option.context;
        },
        getCurrentPopupKwargs: (state)=>{
            return state.current_popup_option.kwargs;
        },
    },
    actions: {
        openPopup(new_option:PopupOptions) : void {

            //enables a button to behave as toggling, simply with @click="openPopup(new_option)"
            if(new_option.context === this.current_popup_option.context){

                //close/reset
                this.current_popup_option = this.getPopupOptionForReset;

            }else{

                this.current_popup_option = new_option;
            }
        },
        //doesn't seem like .bind() works as callbacks for Vue, so we have individual functions for every pop-up
        closeNavMenuPopup() : void {

            if(this.current_popup_option.context === 'nav_menu'){

                this.current_popup_option = this.getPopupOptionForReset;
            }
        },
        closeLoginRequiredPopup() : void {

            if(this.current_popup_option.context === 'login_required'){

                this.current_popup_option = this.getPopupOptionForReset;
            }
        },
        closeLogInPopup() : void {

            if(this.current_popup_option.context === 'log_in'){

                this.current_popup_option = this.getPopupOptionForReset;
            }
        },
        closeSignUpPopup() : void {

            if(this.current_popup_option.context === 'sign_up'){

                this.current_popup_option = this.getPopupOptionForReset;
            }
        },
        closeCancelConfirmPopup() : void {

            if(this.current_popup_option.context === 'cancel_confirm'){

                this.current_popup_option = this.getPopupOptionForReset;
            }
        },
        closeAllPopups() : void {

            this.current_popup_option = this.getPopupOptionForReset;
        },
    },
});