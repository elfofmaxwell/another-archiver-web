"use strict"; 
$(function() {
    format_upload_date();

    // parse video duration
    const video_duration_items = $('.video-duration');
    video_duration_items.each(parse_duration);

    // get current channel id
    const channel_id = location.pathname.split('/')[2];

    /* draw charts */
    // generate default chart
    function empty_chart (chart_ctx, chart_type) {
        return new Chart(chart_ctx, {
            type: chart_type,
            data: {
                labels: [], 
                datasets: [{
                label: '',
                data: [],
                backgroundColor: [],
                }]
            }
        }); 
    }

    function doughnut_color (color_num) {
        const color_list = []; 
        for (let i=0; i<color_num; i++) {
            color_list.push('hsl('+String(i*360/(color_num+1))+',80%,70%');
        }
        return color_list;
    }


    const talent_chart_ctx = $('#talent-chart').get(0).getContext('2d'); 
    const talent_chart= empty_chart(talent_chart_ctx, 'doughnut');

    const tag_chart_ctx = $('#tag-chart').get(0).getContext('2d'); 
    const tag_chart= empty_chart(tag_chart_ctx, 'doughnut');


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
});