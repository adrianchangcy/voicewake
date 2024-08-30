//web workers don't use "window" API, and TS complains if you use number to store setInterval()'s return value
let myTimer:ReturnType<typeof setInterval>;

self.onmessage = function(event){

    //expect {'action': 'start/stop', 'interval_ms: 0, 'starting_ms': 0}

    if(event.data.action === 'start' || event.data.action === 'stop'){

        clearInterval(myTimer);
    }

    if(event.data.action === 'start'){

        let time_passed_ms = event.data.starting_ms;

        myTimer = setInterval(function(){
            
            time_passed_ms += event.data.interval_ms;
            postMessage(time_passed_ms);
        }, event.data.interval_ms);
    }
};