import EventTypes from '@/types/Events.interface';


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
            }else if(interval < 28){    //fastest transition to '1 month ago', for aesthetic reasons only
                return interval.toString() + ' days ago';
            }

            interval = Math.floor(seconds / 2592000);
            if(interval === 1){
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

export function prettyTimeRemaining(current_ms:number, max_ms:number) : string|false {

    //more optimised version, since visits to newer content will always be more
    //to use: timeDifferenceUTC(new Date('2023-04-26T07:45:22.258243Z'))
    //i.e. can immediately use datetime from Django's Serializer

    const seconds = (max_ms - current_ms) / 1000;
    let interval = 0;

    interval = Math.floor(seconds);
    if(interval < 60 && interval > 1){
        return interval + ' seconds left';
    }else if(interval === 1){
        return interval + ' second left';
    }else if(interval === 0){
        return "Time's up!";
    }else if(interval < 0){
        return false;
    }

    interval = Math.floor(seconds / 60);
    if(interval === 1){
        return interval.toString() + ' minute left';
    }else if(interval < 60){
        return interval.toString() + ' minutes left';
    }

    interval = Math.floor(seconds / 3600);
    if(interval === 1){
        return interval.toString() + ' hour left';
    }else if(interval < 24){
        return interval.toString() + ' hours left';
    }

    interval = Math.floor(seconds / 86400);
    if(interval === 1){
        return interval.toString() + ' day left';
    }else if(interval < 28){    //fastest transition to '1 month left', for aesthetic reasons only
        return interval.toString() + ' days left';
    }

    interval = Math.floor(seconds / 2592000);
    if(interval === 1){
        return interval.toString() + ' month left';
    }else if(interval < 12){
        return interval.toString() + ' months left';
    }


    interval = Math.floor(seconds / 31536000);
    if(interval === 1){
        return interval.toString() + ' year left';
    }

    return interval.toString() + ' years left';
}

export function timeFromNowMS(date:Date) : number {

    return Math.floor(new Date().getTime() - date.getTime());
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

export function getUsername() : string {

    return JSON.parse(document.getElementById('data-username')!.textContent!);
}


