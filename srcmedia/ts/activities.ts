import Tablesort from 'tablesort';

document.addEventListener('DOMContentLoaded', () => {

    // selectors
    const $table = document.getElementById('activity-table') as HTMLElement

    Tablesort($table);

})