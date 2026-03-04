frappe.listview_settings['Item'] = {
    refresh: function(listview) {
        // Inject CSS to remove ellipsis and allow wrapping
        const style = `
            <style>
                /* Target the subject column specifically */
                .list-row-container .list-subject {
                    white-space: normal !important;
                    overflow: visible !important;
                    max-width: auto !important;
                }
                /* Optional: Adjust the link inside for wrapping */
                .list-row-container .list-subject a {
                    white-space: normal !important;
                    display: inline-block;
                    margin-right : 20px;
                    
                }
                /* Ensure the row height expands to fit content */
                .list-row {
                    height: auto !important;
                    min-height: 40px;
                }
            </style>
        `;

        $(listview.page.container).find('style.custom-list-style').remove(); // Clean up old styles
        $('<div class="custom-list-style">').html(style).appendTo(listview.page.container);
    }
};
