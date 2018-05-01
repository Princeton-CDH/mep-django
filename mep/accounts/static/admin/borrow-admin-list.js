$(function(){
    $radios = $('.grp-row input[type="radio"]')
    // bold all of the checked options on page load
    $radios.filter(':checked').parent().css('font-weight', 'bold')
    $radios.change(function(event){
        // unbold all sibling options on change
        $(event.target).parents('ul').find('label').css('font-weight', 'normal')
        // rebold only the selected option
        $(event.target).parent().css('font-weight', 'bold')
    })
})

