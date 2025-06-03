/*global URLify*/

/***
Copied from Django prepopulate and customized to look for a
special class names to control behavior:
 - "prepopulate-noslug": opt out of slugifying the prepopulated content
 - "prepopulate-nopace": clear prepopulated value if source value
   contains spaces. (only valid with prepopulate-noslug)
*/
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
        const prepopulatedField = $(this);

        const populate = function() {
            console.log('populate');
            // Bail if the field's value has been changed by the user
            if (prepopulatedField.data('_changed')) {
                return;
            }

            const values = [];
            $.each(dependencies, function(i, field) {
                field = $(field);
                if (field.val().length > 0) {
                    values.push(field.val());
                }
            });

            let value;
            if (prepopulatedField.attr('class').indexOf('prepopulate-noslug') !== -1) {
                // just use the values without slugifying
                value = values.join(' ');
                if (prepopulatedField.attr('class').indexOf('prepopulate-nospace') !== -1
                    && value.indexOf(' ') !== -1) {
                    value = '';
                }
            } else {
                // default django prepopulate behavior
                value = URLify(values.join(' '), maxLength, allowUnicode);
            }
            prepopulatedField.val(value);
        };

        prepopulatedField.data('_changed', false);
        prepopulatedField.on('change', function() {
            prepopulatedField.data('_changed', true);
        });

        if (!prepopulatedField.val()) {
            $(dependencies.join(',')).on('keyup change focus', populate);
        }
    });
};
