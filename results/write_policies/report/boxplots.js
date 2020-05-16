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
      name: 'async',
      type: 'boxplot',
      data: [{low: 92.76, q1: 172.57, median: 207.14, q3: 253.68, high: 539.94 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: 'unsafe',
      type: 'boxplot',
      data: [{low: 99.24, q1: 177.17, median: 212.87, q3: 258.17, high: 510.32 },
],
      visible: true,
      tooltip: {headerFormat: '<em>Operation {point.key}</em><br/>'}
    },
    
{
      name: 'sync',
      type: 'boxplot',
      data: [{low: 57.61, q1: 117.13, median: 138.06, q3: 168.84, high: 381.13 },
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
