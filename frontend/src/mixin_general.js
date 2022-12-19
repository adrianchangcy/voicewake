export const mixinGeneral = {
    data(){
        return {

        };
    },
    methods: {
        arrayMin(array){
            return array.reduce(function(a, b){
                return Math.min(a, b);
            });
        },
        arrayMax(array){
            return array.reduce(function(a, b){
                return Math.max(a, b);
            });
        },
        troubleshootEventListener(label=''){

            //useful for troubleshooting an element with multiple event listeners
            //tells you which was fired
            //e.g. @click="[doSomething(), troubleshootEventListener('a')]"
            console.log('Event of '+label+' was triggered.');
        },
    },
    
};