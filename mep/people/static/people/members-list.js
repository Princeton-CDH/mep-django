$(document).ready(function() {
    // sections
    let $rolodex = $('.rolodex')
    let $filtersSection = $('.filters')
    let $demographicsSection = $('.demographics.grid')
    // dropdowns/buttons
    let $subscriptionYears = $('.subscription-years.field')
    let $booksBorrowed = $('.books-borrowed.field')
    let $demographics = $('.demographics.field')
    let $cardMembers = $('.card-members.field')
    let $featuredMembers = $('.featured-members.field')
    // bindings
    $demographics.click(() => toggleFilters('demographics'))
    // functions
    let filtersOpen = () => $filtersSection.hasClass('visible')
    let toggleFilters = (page) => filtersOpen() ? closeFilters() : openFilters(page)
    let openFilters = (page) => {
        switch(page) {
            case 'demographics':
                $demographicsSection.show()
                $demographics.addClass('active')
                break;
        }
        $filtersSection.transition('slide')
        $rolodex.css('top', '35rem');
    }
    let closeFilters = () => {
        $('.active.field').removeClass('active')
        $filtersSection.transition('slide')
        $rolodex.css('top', '25rem');
    }
    // start closed
    $filtersSection.transition('slide')
})