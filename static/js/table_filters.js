$(document).ready(function() {
    const backupTable = $('#statusTable').DataTable({ paging: false, info: false, searching: false });

    function filterTable() {
        const selectedTypes = $('.filter-type:checked').map(function() {
            return $(this).val().split(',');
        }).get().flat();

        const selectedResults = $('.filter-result:checked').map(function() {
            return $(this).val().split(',');
        }).get().flat();

        backupTable.rows().every(function() {
            const data = this.data();
            let show = true;

            if (selectedTypes.length) {
                show = selectedTypes.some(val => new RegExp(val.replace('*', '.*'), 'i').test(data[2]));
            }
            if (show && selectedResults.length) {
                show = selectedResults.some(val => new RegExp(val.replace('*', '.*'), 'i').test(data[3]));
            }
            $(this.node()).toggle(show);
        });
    }

    $('.filter-type, .filter-result').on('change', filterTable);
    filterTable();
});
