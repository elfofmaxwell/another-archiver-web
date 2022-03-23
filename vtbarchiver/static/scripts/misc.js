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

function parse_duration () {
    let duration_str = $(this).text().substr(2);
    let parsed_time_list = [];
    let splitor; 
    let splitor_list = ['H', 'M', 'S']; 
    for (splitor of splitor_list) {
        let splitted_list = duration_str.split(splitor); 
        if (splitted_list.length === 2) {
            parsed_time_list.push(splitted_list[0].padStart(2, '0'));
        }
        duration_str = splitted_list[splitted_list.length-1];
    }
    let parsed_str = ''; 
    parsed_str += parsed_time_list.join(':');
    console.log(parsed_time_list)
    $(this).text(parsed_str)
}


function parse_tag_list (tagify_obj, submit_input_jq_obj) {
    let tag_value = tagify_obj.value;
    let single_tag;
    let tag_name_list = [];
    for (single_tag of tag_value) {
        tag_name_list.push(single_tag.value);
    }
    let parsed_str = tag_name_list.join(',');
    submit_input_jq_obj.val(parsed_str);
}


function tag_href (tag_type, tag_value) {
    return '/videos/search?'+tag_type+'='+encodeURIComponent(tag_value);
}


function tagify_ajax_wrapper (tagify_obj, tag_type) {
    function input_ajax (e) {
        let input_value = e.detail.value;
        tagify_obj.whitelist = null;

        controller && controller.abort();
        controller = new AbortController();
        
        tagify_obj.loading(true).dropdown.hide();

        $.getJSON('/management/_get-tag-suggestion', {
            "tag-type": tag_type, 
            "query-str": input_value
        }).done( function (parsed_data) {
            tagify_obj.whitelist = parsed_data.suggestions;
            tagify_obj.loading(false).dropdown.show(input_value);
        })
        
    }
    return input_ajax;
}