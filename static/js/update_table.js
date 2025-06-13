function parseDate(dateString) {
    const match = dateString.match(/\/Date\((\d+)\)\//);
    return match ? new Date(parseInt(match[1])).toLocaleString() : dateString;
}

function parseDetail(detailString) {
    try {
        const jsonString = detailString.replace(/^-\s*/, '');
        const detail = JSON.parse(jsonString);
        return {
            lastModified: detail.lastModified ? parseDate(detail.lastModified) : 'N/A',
            resourceGroup: detail.resourceGroup || 'N/A',
            security: detail.security ?? 'N/A',
            osType: detail.osType || 'N/A',
            critical: detail.critical ?? 'N/A'
        };
    } catch (e) {
        console.error('Error parsing detail:', e, detailString);
        return { lastModified: 'Error', resourceGroup: 'Error', security: 'Error', osType: 'Error', critical: 'Error' };
    }
}

$(document).ready(function() {
    const updateAssessmentRows = [];

    $('#backupTableBody tr').each(function() {
        const row = $(this);
        const type = row.find('td:nth-child(3)').text().trim();
        if (type === 'UpdateAssessment') {
            const fecha = row.find('td:nth-child(1)').text();
            const vmName = row.find('td:nth-child(2)').text();
            const detailText = row.find('td:nth-child(5)').text();
            const parsed = parseDetail(detailText);
            updateAssessmentRows.push({ fecha, vmName, ...parsed });
            row.remove();
        }
    });

    const updateTableBody = $('#updateAssessmentTableBody');
    updateAssessmentRows.forEach(row => {
        updateTableBody.append(`<tr>
            <td>${row.fecha}</td><td>${row.vmName}</td><td>${row.lastModified}</td>
            <td>${row.resourceGroup}</td><td>${row.security}</td><td>${row.osType}</td><td>${row.critical}</td>
        </tr>`);
    });

    $('#updateAssessmentTable').DataTable({ paging: false, info: false, searching: false });
});
