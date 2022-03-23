'use strict'
format_upload_date();

let video_duration_items = $('.video-duration');
video_duration_items.each(parse_duration);

// The DOM element you wish to replace with Tagify
let input = document.querySelector('input[name=talent_list]');
let stream_type = document.querySelector('input[name=stream_type]');

// initialize Tagify on the above input node reference
let talent_tags = new Tagify(input, {whitelist: []})
let stream_type_tags = new Tagify(stream_type, {whitelist: []})

// ajax for tagify
let controller;
let talent_input_ajax = tagify_ajax_wrapper(talent_tags, 'talents')
talent_tags.on('input', talent_input_ajax)

let type_input_ajax = tagify_ajax_wrapper(stream_type_tags, 'tags')
stream_type_tags.on('input', type_input_ajax)



// parse tags
let parsed_talent_form = $('#parsed-talent-form');
parsed_talent_form.submit(function () {
    parse_tag_list(talent_tags, $('#parsed-talents'));
});

let parsed_stream_form = $('#parsed-stream-form');
parsed_stream_form.submit(function () {
    parse_tag_list(stream_type_tags, $('#parsed-stream'));
});


// badges as href for search
$(function () {
    $('.talent-badge').click(function () {
        document.location.assign(tag_href('talents', $(this).text()));
    })

    $('.type-badge').click(function () {
        document.location.assign(tag_href('tags', $(this).text()));
    })

    $('#archived-video-modal').on('hidden.bs.modal', function() {
        $('#archived-video-player').trigger('pause');
    })
})