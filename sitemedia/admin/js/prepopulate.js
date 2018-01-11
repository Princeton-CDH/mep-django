/*global URLify*/

/***
Copied from Django prepopulate and customized to look for a
special class name "prepopulate-noslug" to opt out of slugifying the
prepopulated content.

*/

(function($) {
    'use strict';
    $.fn.prepopulate = function(dependencies, maxLength, allowUnicode) {
        /*
            Depends on urlify.js
            Populates a selected field with the values of the dependent fields,
            URLifies and shortens the string.
            dependencies - array of dependent fields ids
            maxLength - maximum length of the URLify'd string
            allowUnicode - Unicode support of the URLify'd string
        */
        return this.each(function() {
            var prepopulatedField = $(this);

            var populate = function() {
                // Bail if the field's value has been changed by the user
                if (prepopulatedField.data('_changed')) {
                    return;
                }

                var values = [];
                $.each(dependencies, function(i, field) {
                    field = $(field);
                    if (field.val().length > 0) {
                        values.push(field.val());
                    }
                });

                var value;
                if (prepopulatedField.attr('class').indexOf('prepopulate-noslug') !== -1) {
                    // just use the values without slugifying
                    value = values.join(' ');
                } else {
                    // default django prepopulate behavior
                    value = URLify(values.join(' '), maxLength, allowUnicode);
                }
                prepopulatedField.val(value);
            };

            prepopulatedField.data('_changed', false);
            prepopulatedField.change(function() {
                prepopulatedField.data('_changed', true);
            });

            if (!prepopulatedField.val()) {
                $(dependencies.join(',')).keyup(populate).change(populate).focus(populate);
            }
        });
    };
})(grp.jQuery);