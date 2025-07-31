<template>
    <div class="pt-8 pb-8 px-2">

        <VTitle propFontSize="l" class="pb-6">
            <template #titleDescription>
                <span>What's your username?</span>
            </template>
        </VTitle>

        <VInput
            propElementId="set-username"
            propLabel="Username"
            propPlaceholder=""
            :propMaxLength="propUsernameMaxLength"
            :propHasTextCounter="true"
            :propIsRequired="true"
            :propHasStatusText="true"
            :propStatusText="username_validation_status_text"
            :propIsError="username_validation_has_error"
            :propIsOk="username_is_ok === true"
            :propIsLoading="is_username_check_loading"
            :propAllowWhitespace="false"
            @hasNewValue="validateUsername($event)"
        />

        <div class="mt-6 pl-2">
            <p class="text-base">You can use full stops ('.') and underscores ('_') among letters and numbers.</p>
        </div>

        <!--main action-->
        <div class="mt-6 h-fit">
            <VActionSpecial
                @click.stop="submitUsernameChange()"
                :propIsEnabled="canSubmitNewUsername"
                propElement="button"
                type="button"
                propElementSize="m"
                propFontSize="l"
                class="w-full"
            >
                <VLoading
                    v-if="is_submitting"
                    prop-element-size="m"
                    prop-colour-class="border-theme-black"
                    class="mx-auto"
                >
                    <span class="pl-2">Saving...</span>
                </VLoading>

                <span v-else class="mx-auto">
                    Set username
                </span>
            </VActionSpecial>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VInput from '@/components/small/VInput.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VLoading from '@/components/small/VLoading.vue';
    import VTitle from '@/components/small/VTitle.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from '@/wrappers/notify_wrapper';
    import { usePageRefreshTriggerStore } from '@/stores/PageRefreshTriggerStore';
    import axios from 'axios';

    export default defineComponent({
        name: "UserOptionsApp",
        data() {
            return {
                page_refresh_trigger_store: usePageRefreshTriggerStore(),

                controller: new AbortController(),

                username_string:"",
                username_validation_status_text: "",
                username_validation_has_error: false,
                username_is_ok: false,
                username_check_timeout: null as number|null,

                is_username_check_loading: false,
                is_submitting: false,
            };
        },
        props: {
            propUsernameMaxLength: {
                type: Number,
                default: 30
            },
        },
        computed: {
            canSubmitNewUsername() : boolean {

                return this.is_username_check_loading === false && this.is_submitting === false;
            },
        },
        methods: {
            newRegExp() : RegExp {

                //either entirely letters and numbers only,
                //or start and end with letters and numbers with possible '_' and '.' in between
                //with the addition of {1,30} for condition 1, constant 120+ steps becomes 6 steps
                //if '_' or '.', cannot continue with another '_' nor '.'

                //remember to remove '\' from string below if deciding to use as literal RegExp

                const default_regex = "(^[a-zA-Z0-9]{1," +
                    this.propUsernameMaxLength.toString() +
                    "}$)|(^[a-zA-Z0-9](_(?!(\\.|_))|\\.(?!(_|\\.))|[a-zA-Z0-9]){0," +
                    (this.propUsernameMaxLength - 2).toString() +
                    "}[a-zA-Z0-9]$)";

                //we use global flag, even though irrelevant, to gain access to .lastIndex on match for showing character error
                //is always >= 0, but it will never restart from 0, so we must restart it ourselves
                return new RegExp(default_regex, "g");
            },
            async checkRegExpForDetailedErrorMessage(new_value:string) : Promise<string> {

                //directly related to newRegExp()
                //because these are not mentioned to keep the tip simple, we only share these as errors when encountered

                if(/^\./.test(new_value) === true){

                    return "Cannot start with '.' for usernames.";

                }else if(/\.$/.test(new_value) === true){

                    return "Cannot end with '.' for usernames.";

                }else if(/^_/.test(new_value) === true){

                    return "Cannot start with '_' for usernames.";

                }else if(/_$/.test(new_value) === true){

                    return "Cannot end with '_' for usernames.";

                }else if(/\._/.test(new_value) === true){

                    return "'.' and '_' cannot be next to each other.";

                }else if(/_\./.test(new_value) === true){

                    return "'_' and '.' cannot be next to each other.";

                }else if(/\.\./.test(new_value) === true){

                    return "'.' and '.' cannot be next to each other.";

                }else if(/__/.test(new_value) === true){

                    return "'_' and '_' cannot be next to each other.";

                }else{

                    //here, '.' does not need '\'
                    const bad_char_index = new_value.search(/[^a-zA-Z0-9._]/);
                    const bad_char = new_value.charAt(bad_char_index);

                    return "Cannot use '" + bad_char + "' in usernames.";
                }
            },
            async resetUsernameRelatedValues() : Promise<void> {

                this.username_string = "";
                this.username_validation_status_text = "";
                this.username_validation_has_error = false;
                this.username_is_ok = false;

                this.username_check_timeout !== null ? window.clearTimeout(this.username_check_timeout) : null;
                this.username_check_timeout = null;
                this.controller.abort();
                this.controller = new AbortController();
            },
            async validateUsername(new_value:string) : Promise<void> {

                await this.resetUsernameRelatedValues();

                //do nothing if there is no text
                if(new_value.length === 0){

                    this.is_username_check_loading = false;
                    return;
                }

                this.is_username_check_loading = true;

                //has text
                this.username_check_timeout = window.setTimeout(async () => {

                    //must not have any whitespace
                    //do not make this too complicated, it is easier to just send email and see if user receives it
                    if(this.newRegExp().test(new_value) === true){

                        this.username_string = new_value;
                        this.username_is_ok = false;
                        this.username_validation_has_error = false;
                        this.username_validation_status_text = "";

                        await this.checkUsernameExists();

                    }else if(/\s+/g.test(new_value) === true){

                        this.username_string = "";
                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "Please remove all spaces.";
                        this.is_username_check_loading = false;

                    }else{

                        //will reach here if the problem is from regex
                        this.username_string = "";
                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = await this.checkRegExpForDetailedErrorMessage(new_value);
                        this.is_username_check_loading = false;
                    }

                }, 400);
            },
            async checkUsernameExists() : Promise<void> {

                if(this.is_submitting === true){

                    return;
                }

                this.username_is_ok = false;
                this.is_username_check_loading = true;
                this.username_validation_has_error = false;

                const url = window.location.origin + "/api/users/username/get/" + this.username_string;

                await axios.get(url, {
                    signal: this.controller.signal
                })
                .then((result:any) => {

                    if(result.data['data']['username'] !== this.username_string){

                        //don't do anything with stale requests
                        //luckily this edge case was caught
                        return;

                    }else if(result.data['data']['exists'] === false){

                        this.username_is_ok = true;
                        this.username_validation_has_error = false;
                        this.username_validation_status_text = "That username is available!";

                    }else{

                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "That username is already taken.";
                    }

                    this.is_username_check_loading = false;
                })
                .catch((error:any) => {

                    if(axios.isCancel(error)){

                        //currently only cancelled on input change, so not an actual error, i.e. do nothing
                        return;
                    }

                    this.username_is_ok = false;
                    this.username_validation_has_error = true;
                    this.username_validation_status_text = "An error had occurred. Try again later.";

                    this.is_username_check_loading = false;

                    let error_text = '';

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        title: 'Username check failed',
                        text: error_text,
                        type: 'error',
                    }, 2000);
                });
            },
            async submitUsernameChange() : Promise<void> {

                if(this.is_submitting === true){

                    return;
                }

                //no need to proceed if error on validating username
                if(this.username_is_ok === false){

                    if(this.username_string.length === 0){

                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "Please enter a username.";
                    }

                    return;
                }

                this.is_submitting = true;

                let data = new FormData();
                data.append("username", this.username_string);

                await axios.post(window.location.origin + "/api/users/username/set", data)
                .then((result:any) => {

                    if(result.data['data']['exists'] === false){

                        //doing this will refresh all open tabs/pages for us
                        this.page_refresh_trigger_store.$patch({
                            refresh_context: "new_username"
                        });

                        //redirect to home page without storing current URL
                        window.location.replace(window.location.origin);

                    }else{

                        //username is taken
                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = result.data['message'];

                        this.is_submitting = false;
                    }
                })
                .catch((error: any) => {

                    this.is_submitting = false;

                    let error_text = '';

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        title: 'Setting username failed',
                        text: error_text,
                        type: 'error',
                    }, 2000);
                });
            },
        },
        mounted(){

        }
    });
</script>