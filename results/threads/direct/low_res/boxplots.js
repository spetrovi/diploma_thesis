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
      categories: ['random_write', 'random_discard', ],
      title: {text: 'Operation'}
    }],
    yAxis: [{
      labels: { formatter: function () {return this.value;}},
      title: {text: 'Throughput [MB/s]'}
    }],
    tooltip: {shared: true},
    
    series: [{
      name: 'default',
      type: 'boxplot',
      data: [{low: 6.99, q1: 116.82, median: 166.24, q3: 229.1, high: 953.87 },
{low: 230.02, q1: 769.08, median: 812.9, q3: 902.03, high: 1184.67 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '1',
      type: 'boxplot',
      data: [{low: 9.08, q1: 107.79, median: 149.48, q3: 221.91, high: 1130.06 },
{low: 90.49, q1: 696.1, median: 761.61, q3: 847.4, high: 1438.11 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '3',
      type: 'boxplot',
      data: [{low: 11.74, q1: 181.42, median: 247.74, q3: 287.65, high: 1366.39 },
{low: 172.02, q1: 1024.35, median: 1214.61, q3: 1353.09, high: 1905.29 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '2',
      type: 'boxplot',
      data: [{low: 6.48, q1: 164.48, median: 239.78, q3: 281.05, high: 1241.21 },
{low: 175.99, q1: 902.4, median: 1074.84, q3: 1214.67, high: 1739.94 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '5',
      type: 'boxplot',
      data: [{low: 4.89, q1: 163.87, median: 267.29, q3: 321.38, high: 1400.84 },
{low: 210.57, q1: 805.61, median: 1074.44, q3: 1257.22, high: 2080.64 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '4',
      type: 'boxplot',
      data: [{low: 4.12, q1: 189.02, median: 256.41, q3: 306.05, high: 1664.54 },
{low: 176.9, q1: 968.68, median: 1230.05, q3: 1374.26, high: 2090.99 },
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
