var boxplots;
$(document).ready(function () {boxplots= new Highcharts.Chart({
    chart: {
      zoomType: 'xy',
      width: 1200,
      height: 600,
      backgroundColor: '#F2F2F2',
      renderTo: 'boxplots'
    },
    title: {text: 'Total througput'},
    xAxis: [{
      categories: ['random_write', ],
      title: {text: 'Operation'}
    }],
    yAxis: [{
      labels: { formatter: function () {return this.value;}},
      title: {text: 'Throughput [MB/s]'}
    }],
    tooltip: {shared: true},
    
    series: [{
      name: 'tail_ssd',
      type: 'boxplot',
      data: [{low: 7.29, q1: 12.27, median: 16.93, q3: 25.38, high: 152.26 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: 'tail_nvme',
      type: 'boxplot',
      data: [{low: 8.27, q1: 13.32, median: 19.08, q3: 29.67, high: 149.68 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: 'vdo_hdd_baseline',
      type: 'boxplot',
      data: [{low: 0.85, q1: 0.97, median: 1.28, q3: 1.87, high: 4.73 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    

    

    ]});
var chart = $('#container').highcharts(),
      type = 1,
      types = ['linear', 'logarithmic'],
      lineColor = 'red';

  $('#boxplots_button').click(function () {
    boxplots.yAxis[0].update({ type: types[type] });
  type += 1;
  if (type === types.length) {
    type = 0;
  }
});

})
