from random import randint
import subprocess
import glob
import numpy as np
from html import *
#from free_space_frag import Free_space_fragmentation
#from extent_distribution import used_space_histogram
#from image import d_image
import csv
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.stats import linregress
import re
import os

colors = {'read': '#f7a35c', 'write': '#90ed7d', 'random_read': '#434348', 'random_write': '#7cb5ec', 'random_discard':'#434348'}

def first(_tuple):
    return _tuple[0]

def untar(source):
    subprocess.call('rm -rf out',shell=True)
    if source[-2:] == 'xz':
        subprocess.call('tar -Jxf '+source+' -C ./',shell=True)

#[(),(),()] -> ([,,,],[,,,])								
def uncurry(l):
    x = []
    y = []
    for t in l:
        x.append(t[0])
        y.append(t[1])
    return (x,y)

def create_button(name):
        button = read_file('templates/button.js')
        button = str(name + "_button").join(button.split("XXX_ID_XXX"))
        button = str(name + '''.yAxis[0].update({ type: types[type] });''').join(button.split("XXX_chart_button_XXX"))
        return button
        
def read_file(name):
  try:
    f = open(name,'r')
    str_ = f.read()
    f.close()
  except:
    return ''
  return str_

def eval_op(op):
    op_dict = {'read':1,'write':2,'random_read':3,'random_write':4,'random_discard':5}
    return op_dict[op]

def op_sort((op,x)):    
    return eval_op(op)

def op_sort_boxplot(boxplot):
    return eval_op(boxplot.op)

def process_files(bw_files, offset, log_window=1.0, bs=10000):
    mask = {'append':'write', 'random_write':'random_write', 'random_read':'random_read', 'read':'read', 'create':'create', 'delete':'delete', 'random_discard':'random_discard'}
    blacklisted = ['create']
    result = {}
    separate = []


    if len(bw_files) == 1:
        operation = {}
        bws = []
        times = []
        with open(bw_files[0], "rb") as csvfile:
            datareader = csv.reader(csvfile)
           
            datareader = [row for row in datareader if float(row[0]) >= offset[0]]
            datareader = [row for row in datareader if float(row[0]) <= offset[1]]

            for i, row in enumerate(datareader):
                name = row[2].strip()
                name = mask[name]
                if name not in blacklisted and name not in operation: operation[name] = ([],[])
                time = float(row[0])
                bw = float(row[1])/1024
                operation[name][0].append(time)
                operation[name][1].append(bw)
        return operation
    
    for fn in bw_files:
        operation = {}
        raw_bws = []
        appended = [-1]
        st_avg = 0
        with open(fn, "rb") as csvfile:
            datareader = csv.reader(csvfile)
           
            #datareader = [row for row in datareader if float(row[0]) >= offset[0]]
            #datareader = [row for row in datareader if float(row[0]) <= offset[1]]

            for i, row in enumerate(datareader):
                name = row[2].strip()
                name = mask[name]
                if name not in blacklisted and name not in operation: operation[name] = [[]]
                time = float(row[0])
                if len(row) == 4:
                    bs = int(row[3])
                bw = float(row[1])/1024
                raw_bws.append(bw)
                completion_time = 1/((bw*1024)/(bs/1024))
                slot_start = int(time/log_window)
                slot_end = slot_start + int(completion_time/log_window) 

                if name not in blacklisted and len(operation[name])-1 < slot_end:
                   operation[name] += [[] for i in range(slot_end-len(operation[name])+1)]

                if name not in blacklisted and len(operation[name]) >= slot_end:
                    if slot_start == slot_end:
                            operation[name][slot_start].append(bw)
                    for s in range(slot_start, slot_end):
                            operation[name][s].append(bw)
        
        separate.append(operation)
                
        
    master = {}
    for item in separate:
        for key, data in item.items():
            #print data
            #print '\n\n'
            data2 = []
            for i in data:
                if i: 
                    data2.append(np.average(i))
                else: data2.append(0)
    
            #print data2
            #print '\n\n\n\n'
            if key not in master:
                master[key] = data2
            else:
                for i, elem in enumerate(data2):
                    if i < len(master[key]):
                        master[key][i] += elem
                    else:
                        master[key].append(elem)
        #print master['random_write']
        #print '\n\n\n next one\n'
        
       
    for key, data in master.items():
        data = data[int(offset[0]//log_window):]
        x = [i for i, y in enumerate(data) if y != 0 ]
        data = filter(lambda x: not not x  , data)
        x = map(lambda c: c * log_window, x)
        master[key] = (x, data)
   
    #print master['random_write']
    return master


#returns value of the given parameter
def get_value(string, parameter):
	res = filter(lambda x: x.split('=')[0] == parameter, string.split('\n'))[0].split('=')[1:]
	if len(res) > 1: return ' '.join('='.join(res).split('-'))
	return res[0]

class Boxplot:
  def __init__(self, op, (x, data), name):
        self.op = op
        self.name = name
        self.low = str(round(np.min(data) + 0.01, 2))
        self.high = str(round(np.max(data) + 0.01, 2))
        self.q1 = str(round(np.percentile(data, 25) + 0.01, 2))
        self.q3 = str(round(np.percentile(data, 75) + 0.01, 2))
        self.median = str(round(np.median(data) + 0.01, 2))
        self.stdev = str(round(np.std(data), 2)).split('.')[0]
        self.code = '''{low: ''' + self.low + ''', q1: ''' + self.q1 + ''', median: ''' + self.median + ''', q3: ''' + self.q3 + ''', high: ''' + self.high + ''' },\n'''



class Compare:
  def __init__(self, tars, destination, offset, log_window, label):
    #self.ID = str(randint(0,10000))
    self.ID = '1'
    self.boxplotID = 'boxplots'
    self.destination = destination
    self.tar_names = []
    for tar in tars:
        self.tar_names.append(tar.tar)
    self.tars = tars
    self.offset = offset
    self.log_window = log_window
    self.boxplots = {}
    self.png_boxplots = []
    self.tables = {}
    self.label = label

    for tar in self.tars:
        bw_data = tar.bws

        tar_boxplots = []
        for key, data in bw_data.items():
                if data != []:
                    tar_boxplots.append(Boxplot(key, data, tar.name))
        tar_boxplots.sort(key=op_sort_boxplot)
        self.boxplots[tar.name] = tar_boxplots
        
    self.make_boxplot()
    self.generate_boxplot()
    
  def make_boxplot(self):
        template = read_file('templates/boxplot_fio.js')
        template_element = read_file('templates/boxplot_element.js')
        template = self.boxplotID.join(template.split("XXX_ID_XXX"))
        
        for name, boxplots in self.boxplots.items():
            tics = ''
            for boxplot in boxplots:
                tics += '''\'''' + boxplot.op + '''\', '''
        
        template = tics.join(template.split("XXX_tics_XXX"))
        
        for name, boxplots in self.boxplots.items():
            template_elem = (name).join(template_element.split("XXX_name_XXX"))
            for boxplot in boxplots:
                template_elem = (boxplot.code+'XXX_boxplot_XXX').join(template_elem.split("XXX_boxplot_XXX"))

            template_elem = ''.join(template_elem.split('XXX_boxplot_XXX'))
            template = (template_elem + 'XXX_element_XXX').join(template.split('XXX_element_XXX'))
        template = ''.join(template.split('XXX_element_XXX'))

        template = create_button(self.boxplotID).join(template.split("XXX_chart_button_XXX"))
        f = open(self.destination + self.boxplotID + '.js', 'w')
        f.write(template)
        f.close()

  def generate_boxplot(self):
        ID_cur = self.ID+'_compare_boxplots.png'


        #Divide data by operations
        operation = {}
        for tar in self.tars:
            for key, x in tar.bws.items():
                if key in operation:
                    operation[key].append((tar.name, x))
                else:
                    operation[key] = [(tar.name, x)]

        for op, tests in operation.items():
            ID = op + ID_cur
            self.tables[ID] = []
            fig, ax = plt.subplots()
            ax.grid()
            ax.set_ylabel('Throughput [MB/s]')
            ax.set_xlabel(self.label)
            ax.set_title('Throughput of ' + op)

            vectors = []
            ticks = []
            positions = []
            i = -1
            for (name, x) in tests:
                if name == 'unsafe': name = 'async-unsafe'
                i += 1
                vectors.append(x[1])
                ticks.append(name)
                positions.append(i)
                
                self.tables[ID].append(Boxplot(op, x, name))
            #ax.set_yscale('log')
            #ax.set_ylim(bottom=0, top=60)
            ax.boxplot(vectors, positions)
            ax.set_xticklabels(ticks)                
            plt.savefig(self.destination + ID, bbox_inches='tight')
    
            plt.close()
            self.png_boxplots.append(ID)

            




class Tar:
    def __init__(self, tar, destination, offset, log_window, smooth, chart_vdostats, lim_y):
        self.destination = destination
        self.tar = tar
        self.tar_name = tar.split('/')[-1:][0][:-7]
        self.properties = read_file(self.tar[:-7]+'.properties')
        self.fsystem = get_value(self.properties,'filesystem')
        self.host = get_value(self.properties,'hostname').split('.')[0]
        self.image_ID = ''
        self.offset = offset#in seconds
        self.table = []
        self.log_window = log_window
        self.smooth = smooth
        self.vdoconfig = ['']
        self.chart_vdostas = chart_vdostats
        self.lim_y = lim_y
        self.name = tar.split('/')[-1].split('-')[-1].rstrip('.tar.xz')
        self.process()



    def process(self):
    	untar(self.tar)
    	#self.image_ID = d_image(self.fsystem, self.destination)
        self.image_ID = 'tar_' + str(randint(0,1000))
        self.bw_files = glob.glob('./out/*bw*.csv')
        if os.path.exists('./out/vdoconfig'):
            self.vdoconfig = read_file('./out/vdoconfig').split('\n')
        recipe = get_value(self.properties,'recipe').split('--')
        blocksize = 10000*1024
        for param in recipe:
            if 'blocksize' in param:
                blocksize = int(param.split('_')[1])*1024

        self.bws = process_files(self.bw_files, self.offset, self.log_window, blocksize)
        self.bw_plot = self.generate_bw_plot()
        self.histograms = self.generate_histogram()
        self.boxplots = self.generate_boxplot()
    	self.vdo_plot = self.generate_vdo_plot()
    	self.threads_plot = self.generate_threads_plot()
        #self.threads_plot = ''
    	self.usage_plot = self.generate_usage_plot()
    	self.extents_ID= 'afaf'#used_space_histogram('./out/fie_data', self.destination)
    	self.image_log = read_file('./out/log.out')
    	self.image_recipe = read_file('./out/recipe')

    	subprocess.call('rm -rf out',shell=True)

    def generate_usage_plot(self):
        ID_cur = self.image_ID+'_usage.png'
        return ID_cur
        recipe = get_value(self.properties,'recipe').split('--')
        for param in recipe:
            if 'report-interval' in param:
                interval = int(param.split('_')[1])


        contents = read_file('./out/df_log.out').split('\n')[:-1]#[8:-3]
        percents = map(lambda x: int(x.split('%')[0].split(' ')[-1:][0]),contents)
        x = [interval*i for i in range(len(percents))]

        fig, ax = plt.subplots()
        ax.plot(x,percents)
        ax.set_ylabel('Used space [%]')
        ax.set_xlabel('Time [s]')
	    #ax.set_ylim([0,0.1])
        ax.grid()
        #fig.set_size_inches(4, 3)
        plt.savefig(self.destination+ID_cur, bbox_inches='tight')
        return ID_cur

    def generate_vdo_plot(self, filename='./out/vdostats'):
        ID_cur = self.image_ID+'_vdostats'
        if not read_file(filename):
            return ID_cur

        values = {}
        #prepare empyt lists:
        for val in self.chart_vdostas:
            values[val] = []

        device = re.findall('/dev/mapper/\S+ :', read_file(filename))[0]
        vdostats = read_file(filename).split(device)[1:]
        for report in vdostats:
            rep = report.split('\n')
            for line in rep:
                name = line.split(':')[0].strip()
                if name in values:
                    val = line.split(':')[1].strip()
                    #most of the values are in 4k blocks, so turning them to GBs
                    if name != 'current VDO IO requests in progress':
                        val = round((float(val)*4096)/(1024*1024*1024), 4)
                    else:
                        val = float(val)
                    values[name].append(val)

        recipe = get_value(self.properties,'recipe').split('--')
        for param in recipe:
            if 'report-interval' in param:
                interval = int(param.split('_')[1])
        
        if 'current VDO IO requests in progress' in values:
            #plot queue chart on separate fig
            fig, ax = plt.subplots()
            ax.set_ylabel('IOs [4k]')
            ax.set_xlabel('Time [s]')
            ax.grid()

            y = values['current VDO IO requests in progress']
            x = [interval*i for i in range(len(y))]
            ax.plot(x, y, label='current VDO IO requests in progress')
        
            ax.legend(loc='center left')#, bbox_to_anchor=(1, 0.5))
            ax.set_title('queue utilisation')
            plt.savefig(self.destination + ID_cur + '_queue.png', bbox_inches='tight')
            plt.close()

            values.pop('current VDO IO requests in progress')

        fig, ax = plt.subplots()
        ax.set_ylabel('Blocks [GB]')
        ax.set_xlabel('Time [s]')
        ax.grid()
      	#fig.set_size_inches(4, 3)
        for key, y in values.items():
                x = [interval*i for i in range(len(y))]
                ax.plot(x, y, label=key)
                
        ax.legend(loc=2)
        #ax.legend(loc='center left')#, bbox_to_anchor=(1, 0.5))
        ax.set_title('vdostats')
        plt.savefig(self.destination + ID_cur + '.png', bbox_inches='tight')
        plt.close()
        return ID_cur + '.png'

    def generate_threads_plot(self, filename='./out/threads'):
        ID_cur = self.image_ID+'_threads.png'
        if not read_file(filename):
            return ID_cur

        blacklisted = ['indexW', 'reader', 'writer']
        
        values = {}
        threads = read_file(filename).split('grep kvdo')
        for report in threads:
            rep = report.split('\n')
            
            for line in rep:
                elems = filter(lambda x: x!='', line.split(' '))
                if len(elems) < 11: continue
                name = elems[-1].strip('[]').split(':')[1]
                if name in blacklisted: continue
                val = float(elems[2])
                if name in values:
                    values[name].append(val)
                if name not in values:
                    values[name] = [val]

        recipe = get_value(self.properties,'recipe').split('--')
        for param in recipe:
            if 'report-interval' in param:
                interval = int(param.split('_')[1])

        fig, ax = plt.subplots()
        ax.set_ylabel('CPU usage [%]')
        ax.set_xlabel('Time [s]')
        ax.grid()
      	#fig.set_size_inches(4, 3)
        for key, y in values.items():
                x = [interval*i for i in range(len(y))]
                ax.plot(x, y, label=key)

        #VDO threads analysis
        report = threads[len(threads)/2].split('\n')
        self.thread_analysis = ''
        f = open(self.destination+self.image_ID+'VDO_threads_analysis', 'a+')        
        for line in report:
            elems = filter(lambda x: x!='', line.split(' '))
            if len(elems) < 11: continue
            name = elems[-1].strip('[]').split(':')[1]
            if name in blacklisted: continue
            val = float(elems[2])
            
            self.thread_analysis += 'Thread: ' + name + ',Usage: ' + str(val) + '%'

            f.write('Thread: ' + name + ',Usage: ' + str(val) + '%')
            if val > 30 and val < 50: 
                self.thread_analysis += ' OK\n'
                f.write(' OK')
            if val < 30: 
                self.thread_analysis += ' LOW\n'            
                f.write(' LOW')
            if val > 50:
                self.thread_analysis += ' HIGH\n'
                f.write(' HIGH')
            f.write('\n')



        #ax.legend(loc=2)
        ax.set_ylim(bottom=0, top=100)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set_title('CPU usage of VDO threads')
        plt.savefig(self.destination+ID_cur, bbox_inches='tight')
        plt.close()
        return ID_cur


    def generate_histogram(self):
        #template = read_file('templates/histogram.js')
        ID = self.image_ID+'_histogram'
        IDs = []
        
        
        #part_template = read_file('templates/histogram_part.js')
        ID_hist = self.image_ID+'_histogram'
        
				
        hists = {}
        bins = {}

        for key, (x,data) in self.bws.items():
            ID_cur = ID + '_' + key+'.png'
            fig, ax = plt.subplots()
            #hist, bins = np.histogram(data)
            #_bins = map(lambda x: round(x,2), bins)
            
            #plt.xscale('log')
            #bins = 10**(np.arange(0,4))

            ax.hist(data, bins=100, color=colors[key])
            ax.set_title('Throughput histogram of: ' + key)
            ax.grid()
            ax.set_ylabel('Frequency')
            ax.set_xlabel('Throughput [MB/s]')
            #ax.bar(_bins, hist)
            IDs.append(ID_cur)
            plt.savefig(self.destination+ID_cur, bbox_inches='tight')
            plt.close()

        return IDs
        
    def generate_boxplot(self):
        ID_cur = self.image_ID+'_boxplot.png'
   
        fig, ax = plt.subplots()
        ax.grid()
        ax.set_ylabel('Throughput [MB/s]')
        ax.set_xlabel('IO operation')
        ax.set_title('Throughput of IO operations')

        vectors = []
        ticks = []
        positions = []
        i = -1

        #for sorting, lets transform the dict to list of tuples
        operations = []
        for key, x in self.bws.items():
            operations.append((key,x))

        operations.sort(key=op_sort)

        for (key, (xx,x)) in operations:
            i+=1
            vectors.append(x)
            ticks.append(key)
            positions.append(i)

            boxplot_table = []
            boxplot_table.append(key)
            boxplot_table.append(round(np.median(x)))
            boxplot_table.append(round(np.percentile(x, 25)))
            boxplot_table.append(round(np.percentile(x, 75)))
            boxplot_table.append(np.max(x))
            boxplot_table.append(np.min(x))
            boxplot_table.append(round(np.std(x), 2))

            self.table.append(boxplot_table)

        #ax.set_yscale('log')
        ax.set_ylim(bottom=0, top=self.lim_y)
        ax.boxplot(vectors, positions)
        ax.set_xticklabels(ticks)                
        plt.savefig(self.destination + ID_cur, bbox_inches='tight')

        plt.close()
        return ID_cur			


	
    def generate_bw_plot(self):
    	ID_cur = self.image_ID+'_bw.png'
        operation = self.bws

        info_file = open(self.destination+self.tar_name+'.info','w')
	
        fig, ax = plt.subplots()
        ax.grid()
        ax.set_ylabel('Throughput [MB/s]')
        ax.set_xlabel('Time [s]')
        ax.set_title('Throughput of IO operations')
        
        offset_correct = int(self.offset[0])



        for key, (x,y) in operation.items():




            #prepare values
            xx = np.linspace(min(x),max(x), 600)
            
            #y = map(lambda x: x/1000, y) #kb to mb
            info_file.write(key+'\n')
            info_file.write(str(np.median(y))+'\,MB/s\n')
            info_file.write(str(np.mean(y))+'\,MB/s\n')

            # interpolate + smooth
            itp = interp1d(x,y)

            window_size, poly_order = 101, 3
            yy_sg = savgol_filter(itp(xx), window_size, poly_order)

            #actual curve			
            y_curve = list(yy_sg)



            #y_curve = list(itp(xx))
            if self.smooth:
                ax.plot(xx, y_curve, color=colors[key], label=key)
            else:
                ax.plot(x, y, color=colors[key], label=key)
            
            #regression
            #fit = np.polyfit(x,y,2)
            #fit_fn = np.poly1d(fit)
            #y_regression = map(lambda x: fit_fn(x), bins_xx)
	    
        ax.legend()
        ax.set_ylim(bottom=0, top=self.lim_y)
        plt.savefig(self.destination+ID_cur, bbox_inches='tight')
        plt.close()
        info_file.close()
        return ID_cur
    

class Report:
  def __init__(self, paths, destination, offset, log_window, smooth, chart_vdostats, lim_y=500, test_label='Test label'):
    self.destination = destination
#	self.destination = destination+paths[0].split('/')[-1:][0][:-7]+'_vs_'+paths[1].split('/')[-1:][0][:-7]+'/'
    subprocess.call('mkdir '+self.destination,shell=True)
    self.tars = []
    for path in paths:
        try:
            self.tars.append(Tar(path, self.destination, offset, log_window, smooth, chart_vdostats, lim_y))
        except:
            print('Bad tar: ' + path)
    if self.tars:
        self.compare = Compare(self.tars, self.destination, offset, log_window, test_label)
        self.report = self.make_report()
        self.save()


  def save(self):
    f = open(self.destination+'/index.html','w+')
    f.write(str(self.report))
    f.close()	

  def make_report(self):
    r = HTML()
    r.html
    r.head
    r.title('Results of drif_job test')
    r.script('', type='text/javascript', src='http://code.jquery.com/jquery-1.9.1.js')
    r += '</head>'
    r.body
    r.script('', src="http://code.highcharts.com/highcharts.js")
    r.script('', src="http://code.highcharts.com/highcharts-more.js")
    r.script('', src="http://code.highcharts.com/modules/exporting.js")
    r.script('', src="//rawgithub.com/phpepe/highcharts-regression/master/highcharts-regression.js")
#	r.script('', src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.2/jquery.min.js")
    r.script('', src="https://code.highcharts.com/highcharts-3d.js")


    r.link(rel="stylesheet", type="text/css", href="stylesheet.css")
    r.br
    r.font(size='3')

    r += '''<style>
    body {
	 font-family: "Arial", Helvetica, Sans-serif;
    }
    table {
        width:20%;
    }
    table, th, td{
        border: 1px solid black;
        border-collapse: collapse;
        font-size: 14px;
    }
    th, td{
        padding: 5px;
        text-align: left;
    }
    table#t01 tr:nth-child(even) {
        background-color: #eee;
    }
    table#t01 tr:nth-child(odd) {
        background-color:#fff;
    }
    table#t01 th	{
        background-color: white;
        color: black;
    }
    .plot {
        display: inline-block;
    }
    .noborder, .noborder tr, .noborder th, .noborder td {
        border: none;
    }
    #top_bar {
        background-color: #1d3b72;
	padding: 14px 16px;
	margin: 0px 0px 0px 0px;
    }
    .options {
	       float: right;
    }
    .menu {
        display: inline;
        padding: 14px 16px;
        font-size: 30px;
        color: white;

    }
    .animatedFading{ opacity: 0.0; }
    .info_panel {
    padding: 50px;
    }
    .menu a{
        text-decoration: none;
        color: white;

    }
    #fail:hover {
        background-color: #ff0000;
    }
    #pass:hover {
        background-color: #5cb55f;
    }
    #invalid:hover {
        background-color: #F4DC15;
    }
    #needs_review:hover {
        background-color: #eee;
        color: black;
    }
    #name {
	float: left
        text-transform: uppercase;
    }
</style>'''
    r.dt
    r.strong('Results of drift_job test')
    r.br
    r.br
    r.dt.strong('Tar name')
    ul = r.ul
    for i, tar in enumerate(self.tars):
	        ul.li('set' + str(i) + ': ' + tar.tar_name)
	
#	r.dt
#	r.strong('Builds')
#	ul = r.ul
#	for i,tar in enumerate(self.tars):
#	        ul.li('set' + str(i) + ': '+get_value(tar.properties,'build'))
	
	
    r.dt.strong('Machine')

	
    r.dt.strong('Result')

    for tar in self.tars:
        r.script('', type='text/javascript', src=tar.image_ID+'.js')
        r.script('', type='text/javascript', src=tar.extents_ID+'.js')
        r.script('', type='text/javascript', src=self.compare.boxplotID+'.js')
        


    table = r.table
    tr = table.tr
    td = tr.td
	
    for tar in self.tars:
        for line in tar.properties.split('\n'):
            td.li(line)
        td = tr.td

    tr = table.tr
    td = tr.td
	
    for tar in self.tars:
        for line in tar.vdoconfig:
            td.li(line)
        td = tr.td      

		
	#tr = table.tr
    #    for tar in self.tars:
    #    	tr.td.div(id=tar.image_ID, align='left')



#    tr = table.tr
#    for tar in self.tars:
#        	tr.td.img(src=tar.usage_plot, align='left')

    tr = table.tr
    for tar in self.tars:
        	tr.td.img(src=tar.vdo_plot, align='left')

#    tr = table.tr
#    for tar in self.tars:
#        	tr.td.img(src=tar.vdo_plot[:-4]+'_queue.png', align='left')

    
#    try:
#        tr = table.tr
#        td = tr.td

#        for tar in self.tars:
#            for l in tar.thread_analysis.split('\n'):
#                td.li(l)
#            td = tr.td


#        tr = table.tr
#        for tar in self.tars:
#           	tr.td.img(src=tar.threads_plot, align='left')
#    except:
#        pass

    tr = table.tr
    for tar in self.tars:
	        tr.td.img(src=tar.bw_plot, align='left')

    for i in range(len(self.tars[0].histograms)):
        r.br
        table = r.table
                
                        
    #tr = table.tr
    hist_num = len(self.tars[0].histograms) 
    for i in range(0, hist_num):
        tr = table.tr
        for j in range(0, len(self.tars)):
            try:
                tr.td.img(src=self.tars[j].histograms[i], align='left')            
            except:
                continue
        
    tr = table.tr
    for tar in self.tars:
        tr.td.img(src=tar.boxplots, align='left')

    table = r.table
    tr = table.tr
    for ID in self.compare.png_boxplots:
        tr.td.img(src=ID, align='left')

    for ID, data in self.compare.tables.items():
        table = r.table(id='t01')
        tr = table.tr
        tr.th(data[0].op)
        tr.th
        tr.th
        tr.th
        tr.th
        tr.th
        tr.th

        tr = table.tr
        tr.th('test name')
        tr.th('median')
        tr.th('first quartile')
        tr.th('third quartile')
        tr.th('min')
        tr.th('max')
        tr.th('standard deviation')
        tr = table.tr


        for boxplot in data:
            tr = table.tr
            tr.td(boxplot.name)
            tr.td(boxplot.median+'MB/s')
            tr.td(boxplot.q1+'MB/s')
            tr.td(boxplot.q3+'MB/s')
            tr.td(boxplot.low+'MB/s')
            tr.td(boxplot.high+'MB/s')
            tr.td(boxplot.stdev+'MB/s')

    latex_code = ''

    for ID, data in self.compare.tables.items():

        latex_code = """\\begin{tabular}{|l|l|l|l|l|l|l|}
        \hline
        \multicolumn{7}{|l|}{Throughput of """ + data[0].op + """ (MB/s)} \\\ \hline
        test name & median & 1st q. & 3rd q. & min & max & stdev \\\ \hline \n"""

        for boxplot in data:
            latex_code += boxplot.name + ' & '
            latex_code += boxplot.median + ' & '
            latex_code += boxplot.q1 + ' & '
            latex_code += boxplot.q3 + ' & '
            latex_code += boxplot.low + ' & '
            latex_code += boxplot.high + ' & '
            latex_code += boxplot.stdev + ' \\\ \hline\n'
    latex_code += '\end{tabular}'

    r += '<!-- \n' + latex_code + '\n-->'
    #table = r.table
    #tr = table.tr
    #tr.td.div(id=self.compare.boxplotID, align='left')

    #tr = table.tr
    #tr.td.div.button('LinY/LogY', id='boxplots_button', align='left')

    

    return r
