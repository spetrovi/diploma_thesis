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
      name: '400g_defaul',
      type: 'boxplot',
      data: [{low: 0.85, q1: 1.02, median: 1.25, q3: 1.46, high: 35.98 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '80g',
      type: 'boxplot',
      data: [{low: 10.57, q1: 52.13, median: 75.2, q3: 172.26, high: 188.82 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: '400g_increased_cache',
      type: 'boxplot',
      data: [{low: 12.69, q1: 61.8, median: 79.11, q3: 175.89, high: 187.58 },
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
