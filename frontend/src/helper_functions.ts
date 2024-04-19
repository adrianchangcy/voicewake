export function axiosCSRFSetup() : void {

    //seems like we just have to call this function once and it'll be set globally
    //this is proven by how we no longer get 403 error when called once at BaseApp

    const axios = require('axios');

    //your template must have {% csrf_token %}
    const token = document.getElementsByName("csrfmiddlewaretoken")[0];

    if(token === undefined){

        throw new Error('CSRF not found.');
    }

    axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
    axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
}


export function arrayMin(your_array:number[]) : number {

    return your_array.reduce(function(a, b){
        return Math.min(a, b);
    });
}


export function arrayMax(your_array:number[]) : number {

    return your_array.reduce(function(a, b){
        return Math.max(a, b);
    });
}


export function prettyTimePassed(date:Date) : string {

    //more optimised version, since visits to newer content will always be more
    //to use: timeDifferenceUTC(new Date('2023-04-26T07:45:22.258243Z'))
    //i.e. can immediately use datetime from Django's Serializer

    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    let interval = 0;

    if(seconds < 60 && seconds >= 0){
        return 'Few seconds ago';
    }else if(seconds < 0){
        return '';
    }

    interval = Math.floor(seconds / 60);
    if(interval === 1){
        return interval.toString() + ' minute ago';
    }else if(interval < 60){
        return interval.toString() + ' minutes ago';
    }

    interval = Math.floor(seconds / 3600);
    if(interval === 1){
        return interval.toString() + ' hour ago';
    }else if(interval < 24){
        return interval.toString() + ' hours ago';
    }

    interval = Math.floor(seconds / 86400);
    if(interval === 1){
        return interval.toString() + ' day ago';
    }else if(interval < 28){
        //fastest transition to '1 month ago', for aesthetic reasons only
        return interval.toString() + ' days ago';
    }

    interval = Math.floor(seconds / 2592000);
    if(interval < 1){
        //need this, since 2592000 is 30 days, and we are doing < 28
        return '1 month ago';
    }else if(interval === 1){
        return interval.toString() + ' month ago';
    }else if(interval < 12){
        return interval.toString() + ' months ago';
    }

    interval = Math.floor(seconds / 31536000);
    if(interval === 1){
        return interval.toString() + ' year ago';
    }

    return interval.toString() + ' years ago';
}


export function prettyTimeRemaining(current_ms:number, max_ms:number) : string {

    //more optimised version, since visits to newer content will always be more
    //to use: timeDifferenceUTC(new Date('2023-04-26T07:45:22.258243Z'))
    //i.e. can immediately use datetime from Django's Serializer

    const seconds = Math.floor((max_ms - current_ms) / 1000);
    let interval = 0;

    interval = Math.floor(seconds);
    if(interval < 60 && interval > 1){
        return interval + ' seconds';
    }else if(interval === 1){
        return interval + ' second';
    }else if(interval <= 0){
        return '';
    }

    interval = Math.floor(seconds / 60);
    if(interval === 1){
        return interval.toString() + ' minute';
    }else if(interval < 60){
        return interval.toString() + ' minutes';
    }

    interval = Math.floor(seconds / 3600);
    if(interval === 1){
        return interval.toString() + ' hour';
    }else if(interval < 24){
        return interval.toString() + ' hours';
    }

    interval = Math.floor(seconds / 86400);
    if(interval === 1){
        return interval.toString() + ' day';
    }else if(interval < 28){
        //fastest transition to '1 month', for aesthetic reasons only
        return interval.toString() + ' days';
    }

    interval = Math.floor(seconds / 2592000);
    if(interval < 1){
        //need this, since 2592000 is 30 days, and we are doing < 28
        return '1 month ago';
    }else if(interval === 1){
        return interval.toString() + ' month ago';
    }else if(interval < 12){
        return interval.toString() + ' months';
    }

    interval = Math.floor(seconds / 31536000);
    if(interval === 1){
        return interval.toString() + ' year';
    }

    return interval.toString() + ' years';
}


export function timeFromNowMS(date:Date) : number {

    //console.log(new Date()) returns easily readable string
    //console.log(new Date().toISOString()) returns practical string
    //either string can be passed into Date() to create new object
    //e.g.: new Date(datetime_str)
    //we don't do this automatically to enable better reusability
    return Math.floor(new Date().getTime() - date.getTime());
}


export function addSeconds(date:Date, total_s:number) : Date {

    return new Date(
        date.getTime() + (total_s * 1000)
    );
}


export function setPiniaDateObject(date:Date) : string {

    //provides consistence for all to-be-stored Date() in Pinia
    //since Date() --> store into Pinia --> rehydrated --> deserialized into string, not Date()
    return date.toISOString();
}


export function getPiniaDateObject(iso_string:string) : Date {

    //get Date() from string
    //Date() can accept and recognise all strings that it would generate
    return new Date(iso_string);
}


export function prettyCount(number:number) : string {
    
    //thanks
    //https://www.skillthrive.com/hunter/snippets/abbreviate-number-javascript

    let pretty_string = '';

    //handle no-abbrev-needed scenario, i.e. < 1000
    if(number < 1000){

        return number.toString();
    }

    // 2 decimal places => 100, 3 => 1000, etc
    // having this as parameter doesn't seem needed
    // decimal_places = Math.pow(10, decimal_places);
    const decimal_places = 1;

    // Enumerate number abbreviations
    const abbrev = ['K', 'M', 'B', 'T'];

    // Go through the array backwards, so we do the largest first
    for(let i = abbrev.length - 1; i >= 0; i--){

        // Convert array index to "1000", "1000000", etc
        const size = Math.pow(10, (i + 1) * 3);

        // If the number is bigger or equal do the abbreviation
        if(number >= size){
            
            // Here, we multiply by decimal_places, round, and then divide by decimal_places.
            // This gives us nice rounding to a particular decimal place.
            number = (number * decimal_places) / size / decimal_places;
            const number_split = number.toString().split('.');

            // Handle special case where we round up to the next abbreviation
            if(number_split.length === 2){

                if(number >= 1000 && i < abbrev.length - 1){

                    //e.g. when 1000K, do 1M
                    number = 1;
                    i++;

                    pretty_string = number.toString() + abbrev[i];

                }else if(number >= 100){

                    //i.e. when >100K, never do decimals
                    pretty_string = number_split[0] + abbrev[i];

                }else{

                    if(number_split[1].charAt(0) === '0'){

                        //i.e. when 99K, don't do decimal if .0
                        pretty_string = number_split[0] + abbrev[i];

                    }else{

                        //i.e. when 99K, do decimal if not .0
                        pretty_string = number_split[0] + '.' + number_split[1].charAt(0) + abbrev[i];
                    }
                }

            }else{

                if(number >= 1000 && i < abbrev.length - 1){

                    number = 1;
                    i++;
                }

                //no decimal, proceed simply
                pretty_string = number.toString() + abbrev[i];
            }



            // We are done... stop
            break;
        }
    }

    return pretty_string;
}


export function prettyDuration(seconds:number) : string {
    return new Date(
        seconds * 1000
    ).toISOString().substring(14, 19);
}


export function getDataFromTemplateJSONScript(element_id:string) : number|string|boolean|null {

    const target = document.getElementById(element_id);

    if(target === null || target.textContent === null){

        return null;
    }

    return JSON.parse(target.textContent);
}


export function getRandomUUID() : any {

    const { v4: uuidv4 } = require('uuid');
    return uuidv4();
}


export function emailValidatorDjango(email:string) : boolean {

    //we follow Django's EmailValidator to prevent frontend success but backend failure

    //currently using Django 1.5 email regex for easier code
    //https://stackoverflow.com/a/18368609

    //latest version has more complexity that requires serious refactoring into JS
    //https://github.com/django/django/blob/main/django/core/validators.py


    return new RegExp(/(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*|^"([\001-\010\013\014\016-\037!#-[\]-\177]|\\[\001-\011\013\014\016-\177])*")@((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)$)|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$/, 'i').test(email);
}


export function getRandomNumber(min_value:number, max_value:number) : number {

    //Math.random() gives 0 to 1
    //we use 0 to 1 to represent actual range/difference between min and max
    //we then add back min to accurately reflect "starts from min"
    //you can use Math.floor() to ensure int

    return Math.random() * (max_value - min_value) + min_value;
}


export function isPageAccessedByReload() : boolean {

    let is_reload = false;

    const has_referrer = document.referrer.length > 0;

    const entries = performance.getEntriesByType("navigation");

    entries.forEach((entry) => {
        if((entry as PerformanceNavigationTiming).type === "reload"){
            is_reload = true;
        }
    });

    return is_reload || has_referrer;
}


export function isPageAccessedByBackForward() : boolean {

    const entries = performance.getEntriesByType("navigation");

    let is_back_forward = false;

    entries.forEach((entry) => {
        if((entry as PerformanceNavigationTiming).type === "back_forward"){
            is_back_forward = true;
        }
    });

    return is_back_forward;
}


export async function drawCanvasRipples(
    canvas_container_rect:DOMRect,
    canvas_element:HTMLCanvasElement,
    audio_volume_peaks:number[]=[],
    transform_origin:'center'|'bottom'='center',
    ripple_width_px:number=2,
) : Promise<void> {

    //everything must be rounded to non-float values allow css image-rendering to work properly
    //be sure that <canvas> also has css w-full h-full

    if(
        (canvas_container_rect.width === 0 && canvas_container_rect.height === 0) ||
        audio_volume_peaks.length === 0
    ){

        return;
    }

    //get font colour for canvas later
    //when dark mode, colour will change accordingly
    const peak_colour_rgb = getComputedStyle(document.documentElement.getElementsByTagName('body')[0])['color'];

    //use DPI to maintain canvas resolution
    //depending on device, or whether user is zoomed in, DPI can be different
    const dpi = window.devicePixelRatio;

    //ensure ripple also scales with DPI
    ripple_width_px = Math.floor(2 * dpi);

    const canvas_context = canvas_element.getContext('2d') as CanvasRenderingContext2D;
    const ripple_quantity = audio_volume_peaks.length;

    //clear canvas for redraw
    canvas_context.clearRect(0, 0, canvas_element.width, canvas_element.height);

    //canvas width and css width are separate things
    //if they are not equal, you will get stretching, pixelation, etc.
    //we adjust resolution according to DPI, while canvas still behaves within w-full h-full CSS
    canvas_element.width = Math.floor(canvas_container_rect.width * dpi);
    canvas_element.height = Math.floor(canvas_container_rect.height * dpi);

    //spacing between ripples, divided without -1 so we have right-most space
    //what's surprising is that the ripples themselves don't need to be accounted for here
    const spacing = Math.floor(canvas_element.width / (ripple_quantity - 1));

    //recalculate width, with and without DPI
    //this allows us to perfectly fit our rects, and we can then mx-auto it
    const new_canvas_width = (spacing * (ripple_quantity - 1)) + ripple_width_px;
    canvas_element.width = new_canvas_width;
    canvas_element.style.width = (new_canvas_width / dpi).toString() + 'px';

    //canvas must have valid and latest width and height, else this won't be applied
    canvas_context.fillStyle = peak_colour_rgb;

    //use this function to ensure that peaks stay within our range
    function getRipple(
        canvas_height:number,
        audio_volume_peak:number,
        lowest_peak:number=0.05,
        highest_peak:number=1,
    ) : number {

        if(audio_volume_peak < lowest_peak){

            return canvas_height * lowest_peak;

        }else if(audio_volume_peak > highest_peak){

            return canvas_height;

        }else{

            return canvas_height * audio_volume_peak;
        }
    }

    //start drawing

    let ripple_height_px = 0;

    if(transform_origin === 'center'){

        //loop through and draw evenly spaced lines
        //do i=1 for left-most space to already exist
        for(let i = 0; i < ripple_quantity; i++){

            ripple_height_px = getRipple(canvas_element.height, audio_volume_peaks[i]);

            //draw ripple
            canvas_context.fillRect(
                (i * spacing),
                Math.round((canvas_element.height - ripple_height_px) / 2),
                ripple_width_px,
                ripple_height_px
            );
        }

    }else if(transform_origin === 'bottom'){

        //loop through and draw evenly spaced lines
        //do i=1 for left-most space to already exist
        for(let i = 0; i < ripple_quantity; i++){

            ripple_height_px = getRipple(canvas_element.height, audio_volume_peaks[i]);

            //draw ripple
            canvas_context.fillRect(
                (i * spacing),
                canvas_element.height,
                ripple_width_px,
                Math.round(-ripple_height_px)
            );
        }
    }
}


export async function downloadBlob(blob:Blob, name:string) : Promise<void> {

    //downloads Blob into actual file
    //https://dev.to/nombrekeff/download-file-from-blob-21ho

    // Convert your blob into a Blob URL (a special url that points to an object in the browser's memory)
    const blobUrl = URL.createObjectURL(blob);

    // Create a link element
    const link = document.createElement("a");

    // Set link's href to point to the Blob URL
    link.href = blobUrl;
    link.download = name;

    // Append link to the body
    document.body.appendChild(link);

    // Dispatch click event on the link
    // This is necessary as link.click() does not work on the latest firefox
    link.dispatchEvent(
        new MouseEvent('click', { 
            bubbles: true, 
            cancelable: true, 
            view: window 
        })
    );

    // Remove link from body
    document.body.removeChild(link);
}


export function getShortenedString(passed_string:string, max_character_count:number) : string {

    const trimmed_string = passed_string.trim();

    if(trimmed_string.length <= max_character_count){

        return trimmed_string;
    }

    //slice accepts index args, and the character 'end' arg will not be included
    return trimmed_string.slice(0, max_character_count).trim() + "...";
}













