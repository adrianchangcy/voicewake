export const mixinGeneral = {
    data(){
        return {

        };
    },
    methods: {
        arrayMin(your_array:number[]):number{
            return your_array.reduce(function(a, b){
                return Math.min(a, b);
            });
        },
        arrayMax(your_array:number[]):number{
            return your_array.reduce(function(a, b){
                return Math.max(a, b);
            });
        },
    },
};