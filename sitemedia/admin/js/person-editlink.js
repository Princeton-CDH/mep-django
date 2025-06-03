/*
Customize person edit input (dal select2) on account page to generate
a link to the person edit page based on the selection.
*/
// alias jquery to $ for convenience
const $ = jQuery;

$(document).ready(function() {
    // store reference to the form input with the person ids
    var person_select = $('#id_persons');
    // create container for displaying edit links
    var editlinks = $('<div/>').attr('id', 'person-editlink').text('test');
    person_select.parent().append(editlinks);

    // function to update person edit links
    function display_edit_links() {
        // remove any current/outdated edit links
        editlinks.empty();

        // add a new link for each current value
        $(person_select.val()).each(function(idx, person_id) {
            var para, link;
            // create a link within a paragraph and add to the edit links div
            link = $('<a>')
                .attr('target', '_blank')   // open in new tab
                // NOTE: the person edit admin url generated here
                // assumes the site is deployed at /
                // and admin has standard configuration.
                // (If this becomes an issue, we could refactor to generate
                // a template person change URL via Django.)
                .attr('href', '/admin/people/person/' + person_id + '/change/')
                .text('edit')
            para = $('<p/>');
            para.append(link);
            editlinks.append(para);

            // NOTE: in theory it should be possible to get the label
            // from the corresponding select2 element, i.e.
            //     parent().find('.select2-selection__choice')
            // However, that is complicated by the fact that the selection
            // doesn't seem to be populated when select change is fired
            // and the fact that newly added values include extra
            // details in the display (dates, mep id, etc).
        });
    }

    person_select.on('change', function() {
        // update displayed links whenever the selection value changes
        display_edit_links();
    });

    // populate edit links on page load
    display_edit_links();
});