"use strict"; 

// The DOM element you wish to replace with Tagify
const talent_input = $('#new-video-talents').get(0); 
const stream_type = $('#new-video-types').get(0); 

// initialize Tagify on the above input node reference
const talent_tags = new Tagify(talent_input, {whitelist: []});
const stream_type_tags = new Tagify(stream_type, {whitelist: []});

// ajax for tagify
let controller;
const talent_input_ajax = tagify_ajax_wrapper(talent_tags, 'talents');
talent_tags.on('input', talent_input_ajax);

const type_input_ajax = tagify_ajax_wrapper(stream_type_tags, 'tags');
stream_type_tags.on('input', type_input_ajax);





$(function() {
    format_upload_date();

    // parse video duration
    const video_duration_items = $('.video-duration');
    video_duration_items.each(parse_duration);

    // get current channel id
    const channel_id = location.pathname.split('/')[2];

    /* draw charts */

    // external legend plugin
    const getOrCreateLegendList = (chart, id) => {
        const legendContainer = document.getElementById(id);
        let listContainer = legendContainer.querySelector('ul');
      
        if (!listContainer) {
            listContainer = document.createElement('ul');
            listContainer.style.display = 'flex';
            listContainer.style.flexDirection = 'row';
            listContainer.style.flexWrap = 'wrap';
            listContainer.style.margin = 0;
            listContainer.style.padding = 0;

            legendContainer.appendChild(listContainer);
        }
      
        return listContainer;
    };
      
    const htmlLegendPlugin = {
        id: 'htmlLegend',
        afterUpdate(chart, args, options) {
            const ul = getOrCreateLegendList(chart, options.containerID);

            // Remove old legend items
            while (ul.firstChild) {
                ul.firstChild.remove();
            }

            // Reuse the built-in legendItems generator
            const items = chart.options.plugins.legend.labels.generateLabels(chart);

            items.forEach(item => {
                const li = document.createElement('li');
                li.style.alignItems = 'center';
                li.style.cursor = 'pointer';
                li.style.display = 'flex';
                li.style.flexDirection = 'row';
                li.style.marginLeft = '10px';

                li.onclick = () => {
                    const {type} = chart.config;
                    if (type === 'pie' || type === 'doughnut') {
                    // Pie and doughnut charts only have a single dataset and visibility is per item
                        chart.toggleDataVisibility(item.index);
                    } else {
                        chart.setDatasetVisibility(item.datasetIndex, !chart.isDatasetVisible(item.datasetIndex));
                    }
                    chart.update();
                };

                // Color box
                const boxSpan = document.createElement('span');
                boxSpan.style.background = item.fillStyle;
                boxSpan.style.borderColor = item.strokeStyle;
                boxSpan.style.borderWidth = item.lineWidth + 'px';
                boxSpan.style.display = 'inline-block';
                boxSpan.style.height = '10px';
                boxSpan.style.marginRight = '5px';
                boxSpan.style.width = '20px';

                // Text
                const textContainer = document.createElement('p');
                textContainer.style.color = 'var(--bs-secondary)';
                textContainer.style.fontSize = '0.9em';
                textContainer.style.margin = 0;
                textContainer.style.marginRight = '1em';
                textContainer.style.padding = 0;
                textContainer.style.textDecoration = item.hidden ? 'line-through' : '';

                const text = document.createTextNode(item.text);
                textContainer.appendChild(text);

                li.appendChild(boxSpan);
                li.appendChild(textContainer);
                ul.appendChild(li);
            });
        }
    };


    // generate default chart
    function empty_chart (chart_ctx, chart_type, legend_id) {
        let chart_config = {
            type: chart_type,
            data: {
                labels: [], 
                datasets: [{
                label: '',
                data: [],
                backgroundColor: [],
                }]
            }, 
        }

        if (legend_id) {
            chart_config.options = {
                plugins: {
                    htmlLegend: {
                        containerID: legend_id, 
                    }, 
                    legend: {
                        display: false, 
                    },
                }, 
            }; 
            chart_config.plugins = [htmlLegendPlugin];
        }

        return new Chart(chart_ctx, chart_config); 
    }

    function doughnut_color (color_num) {
        const color_list = []; 
        for (let i=0; i<color_num; i++) {
            color_list.push('hsl('+String(i*360/(color_num+1))+',80%,70%');
        }
        return color_list;
    }


    const talent_chart_ctx = $('#talent-chart').get(0).getContext('2d'); 
    const talent_chart= empty_chart(talent_chart_ctx, 'doughnut', 'talent-chart-legends');

    const tag_chart_ctx = $('#tag-chart').get(0).getContext('2d'); 
    const tag_chart= empty_chart(tag_chart_ctx, 'doughnut', 'tag-chart-legends');


    const num_stats_ctx = $('#num-stats').get(0).getContext('2d');
    const num_stats_chart = empty_chart(num_stats_ctx, 'line');

    const duration_stats_ctx = $('#duration-stats').get(0).getContext('2d');
    const duration_stats_chart = empty_chart(duration_stats_ctx, 'line');

    const duration_distr_ctx = $('#duration-distr').get(0).getContext('2d');
    const duration_distr_chart = empty_chart(duration_distr_ctx, 'bar');

    function plot_charts (parsed_data){
        talent_chart.data.labels = parsed_data.talent_stats.talent_name;
        talent_chart.data.datasets[0].data = parsed_data.talent_stats.num;
        talent_chart.data.datasets[0].backgroundColor = doughnut_color(talent_chart.data.labels.length);
        talent_chart.data.datasets[0].hoverOffset = 4;
        talent_chart.update();

        tag_chart.data.labels = parsed_data.tag_stats.stream_type;
        tag_chart.data.datasets[0].data = parsed_data.tag_stats.num;
        tag_chart.data.datasets[0].backgroundColor = doughnut_color(tag_chart.data.labels.length);
        tag_chart.data.datasets[0].hoverOffset = 4;
        tag_chart.update();

        num_stats_chart.data.labels = parsed_data.video_num_stats.week.map((w)=>w.split('T')[0]);
        num_stats_chart.data.datasets[0].data = parsed_data.video_num_stats.num;
        num_stats_chart.data.datasets[0].borderColor = 'rgb(255, 191, 191)';
        num_stats_chart.data.datasets[0].pointBackgroundColor = 'rgb(255, 163, 163)';
        num_stats_chart.data.datasets[0].pointBorderColor = 'rgb(255, 163, 163)';
        num_stats_chart.data.datasets[0].tension = 0.5;
        num_stats_chart.data.datasets[0].drawActiveElementsOnTop = false;
        num_stats_chart.options.scales['x'].ticks.autoSkip = true; 
        num_stats_chart.options.scales['x'].ticks.maxTicksLimit = 20;
        num_stats_chart.options.scales['y'].ticks.autoSkip = true; 
        num_stats_chart.options.scales['y'].ticks.maxTicksLimit = 8;
        num_stats_chart.options.scales['y'].title.text = 'Video Number per Week';
        //num_stats_chart.options.scales['y'].title.display = true;
        num_stats_chart.options.scales['y'].beginAtZero = true;
        num_stats_chart.options.plugins.legend.display = false;
        num_stats_chart.update();

        duration_stats_chart.data.labels = parsed_data.duration_stats.week.map((w)=>w.split('T')[0]);
        duration_stats_chart.data.datasets[0].data = parsed_data.duration_stats.duration.map((d)=>(d/3600).toFixed(2));
        duration_stats_chart.data.datasets[0].borderColor = 'rgb(179, 221, 242)';
        duration_stats_chart.data.datasets[0].pointBackgroundColor = 'rgb(142, 200, 230)';
        duration_stats_chart.data.datasets[0].pointBorderColor = 'rgb(142, 200, 230)';
        duration_stats_chart.data.datasets[0].tension = 0.5;
        duration_stats_chart.data.datasets[0].drawActiveElementsOnTop = false;
        duration_stats_chart.options.scales['x'].ticks.autoSkip = true; 
        duration_stats_chart.options.scales['x'].ticks.maxTicksLimit = 20;
        duration_stats_chart.options.scales['y'].ticks.autoSkip = true; 
        duration_stats_chart.options.scales['y'].ticks.maxTicksLimit = 8;
        duration_stats_chart.options.scales['y'].title.text = 'Video Durations per Week (Hr)';
        //duration_stats_chart.options.scales['y'].title.display = true;
        num_stats_chart.options.scales['y'].beginAtZero = true;
        duration_stats_chart.options.plugins.legend.display = false;
        duration_stats_chart.update();

        duration_distr_chart.data.labels = ['<30', '30-60', '60-90', '90-120', '120-150', '150-180', '>180'];
        duration_distr_chart.data.datasets[0].data = parsed_data.duration_distr.num;
        duration_distr_chart.data.datasets[0].backgroundColor = "rgb(203, 237, 183)";
        duration_distr_chart.options.plugins.legend.display = false;
        duration_distr_chart.options.scales['y'].title.text = 'Times';
        //duration_distr_chart.options.scales['y'].title.display = true;
        duration_distr_chart.update();
    }

    $('.stats-filter').each(function () {
        $(this).click( function () {
            //$('.stats-filter').prop('aria-pressed', "false");
            //$(this).prop('aria-pressed', 'true');

            $('.stats-filter').removeClass('btn-secondary text-light');
            $(this).addClass('btn-secondary text-light');

            let time_delta = 0;
            const time_delta_input = $(this).prop('id').split('-')[1];
            if (Number(time_delta_input)) {
                time_delta = Number(time_delta_input);
            }
            $.getJSON('/api/channel-stats', {
                'channel-id': channel_id,
                'stats-type': "all",
                'time-delta': time_delta, 
            }).done(plot_charts);
        })
    })

    $('#stats-tab').click(() => {
        $('#stats-fit').click();
    });



    /* channel management */
    // auto set hex video id
    const unarchived_field = $('#unarchived-field');
    const unarchive_check =  $('#unarchived-content-check');
    const new_video_id = $('#new-video-form input[name=new-video-id]');
    const new_video_title = $('#new-video-title');
    const new_video_date = $('#new-video-date');
    const new_video_duration = $('#new-video-duration');
    const new_video_thumb = $('#new-video-thumb');
    unarchive_check.change(function () {
        if ($(this).is(':checked')) {
            $.getJSON('/api/get-new-hex-vid').done((parsed_json) => {
                new_video_id.val(parsed_json.new_hex_vid);
            })
            new_video_id.prop('readonly', true);
            unarchived_field.removeClass('d-none');
        } else {
            new_video_id.prop('readonly', false);
            new_video_id.val('');
            unarchived_field.addClass('d-none');
        }
    })
    // set upload date
    $('input[name="new-video-date-picker"]').daterangepicker({
        singleDatePicker: true,
        timePicker: true, 
        locale: {
            format: 'MMMM DD, YYYY, hh:mm A',
        }
    }, function (start, end, label) {
        new_video_date.val(String(start.utc().format()));
    });

    const add_video_btn = $('#add-video-btn');
    add_video_btn.click(() => {
        $('#add-video-warning').empty();
        const duration_reg = /\d{2}\:\d{2}\:\d{2}/
        if ( (!duration_reg.test(new_video_duration.val())) && unarchive_check.is(':checked') ) {
            const invalid_duration_warning = $(document.createElement('div'));
            invalid_duration_warning.text('Invalid duration');
            invalid_duration_warning.addClass('alert');
            invalid_duration_warning.addClass('alert-warning');
            $('#add-video-warning').append(invalid_duration_warning);
            return false
        }
        const parsed_duration = moment.duration(new_video_duration.val());
        // parse tags
        parse_tag_list(talent_tags, $('#parsed-video-talents'));
        parse_tag_list(stream_type_tags, $('#parsed-video-types'));
        $.post('/api/manually-add-video', {
            channel_id: channel_id,
            unarchive_check: unarchive_check.is(':checked'), 
            video_id: new_video_id.val(),
            title: new_video_title.val(), 
            upload_date: new_video_date.val(),
            duration: parsed_duration.toISOString(),
            thumb_url: new_video_thumb.val(),
            talent_names: $('#parsed-video-talents').val(), 
            stream_types: $('#parsed-video-types').val(), 
        }).done((returned_data) => {
            console.log(returned_data);
        });
      })
});