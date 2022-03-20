'use strict'

function set_page_active (current_page) {
    let active_tag = $('#page-tag-'+String(current_page));
    active_tag.addClass('active');
}

function format_upload_date () {
    let upload_date_list = $('.video-upload-date');

    function convert_date_string () {
        let single_date;
        let single_time_stamp;
        let single_date_obj;
        let local_date_str;

        single_date = $(this).text();
        single_time_stamp = Date.parse(single_date); 
        single_date_obj = new Date(single_time_stamp); 
        local_date_str = single_date_obj.toLocaleString();
        $(this).text(local_date_str);
    }

    upload_date_list.each(convert_date_string);
}

function switch_to_add_channel () {
    let add_channel_tab = $('#add-channel-tab'); 
    let add_channel_form_blk = $('#add-channel-form-blk');

    add_channel_tab.removeClass('d-flex');
    add_channel_tab.addClass('d-none');
    add_channel_form_blk.removeClass('d-none');
    add_channel_form_blk.addClass('d-flex');
}