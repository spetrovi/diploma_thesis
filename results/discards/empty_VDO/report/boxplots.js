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
      categories: ['random_discard', ],
      title: {text: 'Operation'}
    }],
    yAxis: [{
      labels: { formatter: function () {return this.value;}},
      title: {text: 'Throughput [MB/s]'}
    }],
    tooltip: {shared: true},
    
    series: [{
      name: '1m',
      type: 'boxplot',
      data: [{low: 44.31, q1: 44.75, median: 44.87, q3: 45.03, high: 46.67 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '4k',
      type: 'boxplot',
      data: [{low: 48.4, q1: 1075.4, median: 1114.18, q3: 1152.95, high: 1334.86 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '128k',
      type: 'boxplot',
      data: [{low: 51.29, q1: 201.6, median: 202.49, q3: 203.29, high: 223.63 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '16k',
      type: 'boxplot',
      data: [{low: 52.48, q1: 935.99, median: 977.27, q3: 1019.96, high: 1111.36 },
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
