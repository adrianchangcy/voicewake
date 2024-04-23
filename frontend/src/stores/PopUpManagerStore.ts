import { defineStore } from 'pinia';



type PopUpContextsTypes = ""|"nav_menu"|"login_required"|"log_in"|"sign_up";

//helps us manage pop-ups
//currently using redundant way of ensuring other pop-ups are closed when one opens
//still manageable because we have limited pop-ups
export const usePopUpManagerStore = defineStore('pop_up_manager', {
    state: ()=>({
        is_logged_in: false,
        current_popup_context: "" as PopUpContextsTypes,
    }),    
    getters: {
        isLoggedIn() : boolean {
            return this.is_logged_in;
        },
        isNavMenuOpen() : boolean {
            return this.current_popup_context === 'nav_menu';
        },
        isLoginRequiredOpen() : boolean {
            return this.current_popup_context === 'login_required';
        },
        isLogInOpen() : boolean {
            return this.current_popup_context === 'log_in';
        },
        isSignUpOpen() : boolean {
            return this.current_popup_context === 'sign_up';
        },
    },
    actions: {
        setIsLoggedIn(new_value:boolean) : void {
            
            this.is_logged_in = new_value;
        },
        openPopUp(new_value:PopUpContextsTypes) : void {

            if(new_value === this.current_popup_context){

                this.current_popup_context = '';

            }else{

                this.current_popup_context = new_value;
            }
        },
        //doesn't seem like.bind() works as callbacks for Vue, so we have individual functions for every pop-up
        closeNavMenuPopUp() : void {

            if(this.current_popup_context === 'nav_menu'){

                this.current_popup_context = '';
            }
        },
        closeLoginRequiredPopUp() : void {

            if(this.current_popup_context === 'login_required'){

                this.current_popup_context = '';
            }
        },
        closeLogInPopUp() : void {

            if(this.current_popup_context === 'log_in'){

                this.current_popup_context = '';
            }
        },
        closeSignUpPopUp() : void {

            if(this.current_popup_context === 'sign_up'){

                this.current_popup_context = '';
            }
        },
        closeAllPopUps() : void {

            this.current_popup_context = "";
        },
    },
});