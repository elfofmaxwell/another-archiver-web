'use strict';
format_upload_date();

const video_duration_items = $('.video-duration');
video_duration_items.each(parse_duration);

// The DOM element you wish to replace with Tagify
const input = document.querySelector('input[name=talent_list]');
const stream_type = document.querySelector('input[name=stream_type]');

// initialize Tagify on the above input node reference
const talent_tags = new Tagify(input, {whitelist: []});
const stream_type_tags = new Tagify(stream_type, {whitelist: []});

// ajax for tagify
let controller;
const talent_input_ajax = tagify_ajax_wrapper(talent_tags, 'talents');
talent_tags.on('input', talent_input_ajax);

const type_input_ajax = tagify_ajax_wrapper(stream_type_tags, 'tags');
stream_type_tags.on('input', type_input_ajax);


// parse tags
const parsed_talent_form = $('#parsed-talent-form');
parsed_talent_form.submit(function() {
  parse_tag_list(talent_tags, $('#parsed-talents'));
});

const parsed_stream_form = $('#parsed-stream-form');
parsed_stream_form.submit(function() {
  parse_tag_list(stream_type_tags, $('#parsed-stream'));
});


// badges as href for search
$(function() {
  $('.talent-badge').click(function() {
    document.location.assign(tag_href('talents', $(this).text()));
  });

  $('.type-badge').click(function() {
    document.location.assign(tag_href('tags', $(this).text()));
  });

  $('#archived-video-modal').on('hidden.bs.modal', function() {
    $('#archived-video-player').trigger('pause');
  });


  const video_id = location.pathname.split('/')[2];
    /* channel management */
  // auto set hex video id
  const unarchived_field = $('#unarchived-field');
  const unarchive_check =  $('#unarchived-content-check');
  const new_video_id = $('#new-video-form input[name=new-video-id]');
  const new_channel_id = $('#new-channel-id');
  const new_video_title = $('#new-video-title');
  const new_video_date = $('#new-video-date');
  const new_video_duration = $('#new-video-duration');
  const new_video_thumb = $('#new-video-thumb');
  // set upload date
  $('input[name="new-video-date-picker"]').daterangepicker({
      autoUpdateInput: false,
      singleDatePicker: true,
      timePicker: true, 
      locale: {
          format: 'MMMM DD, YYYY, hh:mm A',
          cancelLabel: 'Clear', 
      }
  });
  $('input[name="new-video-date-picker"]').on('apply.daterangepicker', function(ev, picker) {
    $(this).val(picker.startDate.format('MM/DD/YYYY hh:mm:ss'));
    new_video_date.val(String(picker.startDate.utc().format()));
  });
  $('input[name="new-video-date-picker"]').on('cancel.daterangepicker', function(ev, picker) {
    $(this).val('');
    new_video_date.val('');
  });



  const update_video_btn = $('#update-video-btn');
  update_video_btn.click(() => {
      $('#update-video-warning').empty();
      const duration_reg = /\d{2}\:\d{2}\:\d{2}/
      if ( (!duration_reg.test(new_video_duration.val())) && new_video_duration.val() ) {
          const invalid_duration_warning = $(document.createElement('div'));
          invalid_duration_warning.text('Invalid duration');
          invalid_duration_warning.addClass('alert');
          invalid_duration_warning.addClass('alert-warning');
          $('#update-video-warning').append(invalid_duration_warning);
          return false
      }
      let parsed_duration = '';
      if ( new_video_duration.val() ){
        parsed_duration = moment.duration(new_video_duration.val()).toISOString();
      }
      $.post('/api/'+video_id+'/manually-update-video', {
          channel_id: new_channel_id.val(),
          title: new_video_title.val(), 
          upload_date: new_video_date.val(),
          duration: parsed_duration,
          thumb_url: new_video_thumb.val()
      }).done((returned_data) => {
          if ( returned_data.result === 'success') {
            location.assign(location.href);
          } else {
            const update_server_warning = $(document.createElement('div'));
            update_server_warning.text('Server says: '+returned_data.message);
            update_server_warning.addClass('alert'); 
            update_server_warning.addClass('alert-warning');
            $('#update-video-warning').append(update_server_warning);
          }
      });
    })
  
  const delete_video_btn = $('#delete-video-btn');
  delete_video_btn.click(function () {
    if (confirm('Are you sure you want delete the video? This would not delete local files. ')) {
      $.get('/api/'+video_id+'/delete-video').done((returned_data) => {
        if ( returned_data.result === 'success') {
          history.back();
        } else {
          const delete_server_warning = $(document.createElement('div'));
          delete_server_warning.text('Server says: '+returned_data.message);
          delete_server_warning.addClass('alert'); 
          delete_server_warning.addClass('alert-warning');
          $('#update-video-warning').append(update_server_warning);
        }
      })
    }
  })
  
  const download_btn = $('#download-btn');
  $.get('/api/downloading').done((returned_data) => {
      if ( returned_data.message === 'downloading' ) {
          download_btn.prop('disabled', true);
      }
  });
  
  download_btn.click(function () {
      $.get('/api/downloading').done((returned_data) => {
          if ( returned_data.message === 'downloading' ) {
            download_btn.prop('disabled', true);
            const downloading_warning = $(document.createElement('div'));
            downloading_warning.text('There is download task running. ');
            downloading_warning.addClass('alert'); 
            downloading_warning.addClass('alert-warning');
            $('#single-video-warning').append(downloading_warning);
          } else {
            $.get('/api/'+video_id+'/download').done((returned_data)=>{
              if ( returned_data.result === 'success' ) {
                download_btn.prop('disabled', true);
                const downloading_warning = $(document.createElement('div'));
                downloading_warning.text(`Start download ${video_id}.`);
                downloading_warning.addClass('alert'); 
                downloading_warning.addClass('alert-success');
              }
            })
          }
      });
  });
});
