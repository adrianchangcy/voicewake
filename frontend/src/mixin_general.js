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
    },
    
};