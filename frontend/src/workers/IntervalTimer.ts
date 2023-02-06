let mytimer:number;

self.onmessage = function(event){

    //expect {'action': 'start/stop', 'interval_ms: 0, 'starting_ms': 0}

    if(event.data.action === 'start' || event.data.action === 'stop'){

        clearInterval(mytimer);
    }

    if(event.data.action === 'start'){

        let time_passed_ms = event.data.starting_ms;

        mytimer = setInterval(function(){
            
            time_passed_ms += event.data.interval_ms;
            postMessage(time_passed_ms);
        }, event.data.interval_ms);
    }
};