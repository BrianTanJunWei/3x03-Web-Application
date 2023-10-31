attachEventToBtnExport()

function attachEventToBtnExport() {
    const bntExportElement = document.querySelector( '.btnExport' )
    bntExportElement.addEventListener( 'click', exportExcel )
}

async function exportExcel() {
    let response = await fetch( '/download_logs_api' )
    let blobResponse = await response.blob()
    const fileName = 'logs.xlsx'
    downloadExcelSilently( blobResponse, fileName )
}
function downloadExcelSilently( blobExcelFile, filename ) {
    const url = window.URL.createObjectURL( blobExcelFile );
    const hiddenAnchor = document.createElement( "a" );
    hiddenAnchor.style.display = "none";
    hiddenAnchor.href = url;
    hiddenAnchor.download = filename;
    document.body.appendChild( hiddenAnchor );
    hiddenAnchor.click();
    window.URL.revokeObjectURL( url );
}