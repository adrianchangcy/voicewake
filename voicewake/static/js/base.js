//uses jquery and jquery UI
//remember that current way of referencing static/base.js is unsecure for production
//refer to link below:
//https://docs.djangoproject.com/en/4.0/howto/static-files/deployment/


jQuery(document).ready(function($){

    //NAVBAR
    // Check for click events on the navbar burger icon
    $("#dropdownNavbarLink").click(function(){
        $("#dropdownNavbar").toggleClass("hidden");
    })

    
    //AUTOCOMPLETE FOR TEXT FIELDS WITH AJAX QUERY TO DB
    $('.reuse_basic_autocomplete').autocomplete({
        //standard autocomplete is 300ms delay (after last keystroke)
        //and 3 or 4 minimum string length before it starts doing API requests
        delay: 300,
        minLength: 3,
        source: function(request, response) {
            //use table_name and column_name attribute to make this autocomplete reusable
            let table_name = $(this.element).attr('table_name');
            let column_name = $(this.element).attr('column_name');
            let search_string = request.term;
            let search_result = [];
            $.ajax({
                url: 'http://127.0.0.1:8000/api/'+table_name,
                data: {
                    search: search_string,
                },
                method: 'GET',
                headers: {
                    'credentials': 'same-origin',
                },
                success: function(data) {
                    if(!data || data.length == 0){
                        //no data, do nothing
                    }else{
                        //doing it this way in hopes that PK id can be preserved and passed to POST later
                        for(let x = 0; x < data.length; x++){
                            let datum = data[x];
                            search_result.push({
                                data: datum,
                                value: datum[column_name],
                            });
                        }
                    }
                    response(search_result);
                },
            })
        }
    });


    //AUDIO CAPTURE
    
});