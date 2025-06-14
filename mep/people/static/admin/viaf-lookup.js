// alias jquery to $ for convenience
const $ = jQuery;

$(document).on('select2:select', function(evt) {
    var data = evt.params.data;
    var target = evt.target;
    // check that it's viaf being cleared and not the other selectors
    if (target.name == 'viaf_id') {
        $('#viaf_uri').attr('href', data.id).text(data.id);
        // show delete button in case previously hidden
        $('#viaf_id-delete').show();
        // SRU search data may include birth/death in the result;
        // set them if present and not zero (i.e. dates unknown)
        // handle separately, since one may be known and not the other
        // otherwise, clear birth and death and attempt to set on save
        if (data.birth && data.birth !== 0) {
            $('input[name="birth_year"]').val(data.birth.substring(0, 4));
        } else {
            $('input[name="birth_year"]').val('');
        }
        if (data.death && data.death != 0) {
            $('input[name="death_year"]').val(data.death.substring(0, 4));
        } else {
            $('input[name="death_year"]').val('');
        }
  }

});


$( document ).ready(function() {
    // add a way to clear selected viaf id
    var span = $('<span>').attr('class', 'grp-tools');
    var del = $('<a>')
        .attr('id', 'viaf_id-delete')
        .attr('class', 'grp-icon grp-delete-handler')
        .attr('title', 'Clear VIAF ID');
    del.on('click', function() {

        $('select[name="viaf_id"]').select2().val(null).trigger("change");
        $('#viaf_uri').attr('href', '').text('');
        $('input[name="birth_year"]').val('');
        $('input[name="death_year"]').val('');
    });
    span.append(del)
    span.insertAfter($('#viaf_uri'));
    if ($('#viaf_uri').text() == '') {
        del.hide();
    }
});
