'use strict';
// video search tags
const talent_search = $('#talent-search').get(0);
const tag_search = $('#tag-search').get(0);

const talent_search_tags = new Tagify(talent_search);
const tag_search_tags = new Tagify(tag_search);

// ajax for tagify
let controller;
const talent_search_ajax = tagify_ajax_wrapper(talent_search_tags, 'talents');
talent_search_tags.on('input', talent_search_ajax);

const tag_search_ajax = tagify_ajax_wrapper(tag_search_tags, 'tags');
tag_search_tags.on('input', tag_search_ajax);


$(function() {
  /* show search information */
  // add display region
  const search_params_display = $(document.createElement('div'));
  const search_area = $('#search-area');
  search_area.after(search_params_display);
  search_params_display.addClass('text-secondary');
  search_params_display.css('font-size', '0.8em');
  search_params_display.html('<div id="search-key"></div><div id="search-tags"></div>');
  const search_key = $('#search-key');
  const search_tags = $('#search-tags');
  // get get request params
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  if (urlParams.get('search-keys')) {
    search_key.text('Searching '+urlParams.get('search-keys'));
  }
  const talent_url = urlParams.get('talents');
  const tag_url = urlParams.get('tags');
  const time_range_url = urlParams.get('time-range');
  const time_descending_url = urlParams.get('time-descending');
  // format request params
  let talent_str = '';
  let tag_str = '';
  let time_range_str = '';
  let time_descending_str = '';
  const display_param_list = [];
  if (talent_url) {
    talent_str = talent_url.split(',').join(', ');
    display_param_list.push(talent_str);
  }
  if (tag_url) {
    tag_str = tag_url.split(',').join(', ');
    display_param_list.push(tag_str);
  }
  if (time_range_url) {
    time_range_str = time_range_url.split(';').map(function(time_str) {
      return moment(time_str).format('MMM D, YYYY');
    }).join(' - ');
    display_param_list.push(time_range_str);
  }
  if (time_descending_url) {
    time_descending_str = 'by upload date (newest): ' + time_descending_url;
    display_param_list.push(time_descending_str);
  }
  // add to html
  if (display_param_list.length > 0) {
    search_tags.text('On '+display_param_list.join('; '));
  }


  // format upload date to local date for each video
  format_upload_date();


  // parse video_duration
  const video_duration_items = $('.video-duration');
  video_duration_items.each(parse_duration);

  // date range picker for search
  $('input[name="datefilter"]').daterangepicker({
    autoUpdateInput: false,
    locale: {
      cancelLabel: 'Clear',
    },
  });

  $('input[name="datefilter"]').on('apply.daterangepicker', function(ev, picker) {
    $('#time-range').val(picker.startDate.format('YYYY-MM-DD') + 'T00:00:00Z;' + picker.endDate.format('YYYY-MM-DD') + 'T00:00:00Z');
    $(this).val(picker.startDate.format('MMMM D, YYYY') + ' - ' + picker.endDate.format('MMMM D, YYYY'));
  });

  $('input[name="datefilter"]').on('cancel.daterangepicker', function(ev, picker) {
    $('#time-range').val('');
    $(this).val(picker.startDate.format('YYYY-MM-DD') + 'T00:00:00Z;' + picker.endDate.format('YYYY-MM-DD'));
  });


  // time descending switch
  const descending_form = $('#time-descending');
  const descending_switch = $('#descending-switch');
  descending_switch.click( function() {
    if (descending_form.val() === 'false') {
      descending_form.val('true');
      descending_switch.html('<i class="iconfont icon-wind-descending"></i> Date added (newest)');
    } else {
      descending_form.val('false');
      descending_switch.html('<i class="iconfont icon-rank"></i> Default');
    }
  });


  // parse tags to submit search
  const search_form = $('#search-form');
  search_form.submit(function() {
    parse_tag_list(talent_search_tags, $('#parsed-talents'));
    parse_tag_list(tag_search_tags, $('#parsed-tags'));
  });

});