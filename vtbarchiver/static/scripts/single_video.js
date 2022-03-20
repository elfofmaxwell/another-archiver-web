'use strict'
// The DOM element you wish to replace with Tagify
let input = document.querySelector('input[name=talent_list]');
let stream_type = document.querySelector('input[name=stream_type]');

// initialize Tagify on the above input node reference
let talent_tags = new Tagify(input)
let stream_type_tags = new Tagify(stream_type)


function close_parse_tag (tagify_obj, submit_input_jq_obj) {
    function parse_tag_list () {
        let tag_value = tagify_obj.value;
        let single_tag;
        let tag_name_list = [];
        for (single_tag of tag_value) {
            tag_name_list.push(single_tag.value);
        }
        let parsed_str = tag_name_list.join(',');
        submit_input_jq_obj.val(parsed_str);
    }

    return parse_tag_list;
}

let parse_talents = close_parse_tag(talent_tags, $('#parsed-talents'));
let parse_stream_type = close_parse_tag(stream_type_tags, $('#parsed-stream'));

let parsed_talent_form = $('#parsed-talent-form');
parsed_talent_form.submit(parse_talents);

let parsed_stream_form = $('#parsed-stream-form');
parsed_stream_form.submit(parse_stream_type);