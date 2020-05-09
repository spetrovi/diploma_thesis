# opts.py - module to parse command line options and output what parameters will be used for this run

import os
import os.path
import sys
import common
from common import rq, file_access_dist, OK, NOTOK


def usage(msg):
    print(msg)
    print('usage: fs-drift.py [ --option value ]')
    print('options:')
    print('-h|--help')
    print('-t|--top-directory')
    print('-S|--starting-gun-file')
    print('-o|--operation-count')
    print('-d|--duration')
    print('-f|--max-files')
    print('-s|--file_size')
    print('-b|--blocksize')
    print('-Y|--fsync')
    print('-y|--fdatasync')
    print('-T|--response-times')
    print('-b|--bandwidth')
    print('-l|--levels')
    print('-D|--dirs-per-level')
    print('-w|--workload-table')
    print('-i|--report-interval')
    print('-+D|--random-distribution')
    print('-+v|--mean-velocity')
    print('-+d|--gaussian-stddev')
    print('-+c|--create_stddevs-ahead')
    print('-c|--compression_ratio')
    print('-p|--pause_file')
    print('+-d|--direct')
    print('-P|--prefix')
    print('-+r|--rawdevice')
    print('-+R|--randommap')
    print('-F|--fill')
    print('-+D|--dedupe-percentage')
    print('-+t|--threads')
    sys.exit(NOTOK)

# command line parameter variables here


starting_gun_file = None
top_directory = '/tmp/foo'
opcount = 0
duration = 1
max_files = 20
file_size = 1024
blocksize = 4
fdatasync_probability_pct = 10
fsync_probability_pct = 20
short_stats = False
levels = 2
dirs_per_level = 3
rsptimes = None
bw = None
workload_table_filename = None
stats_report_interval = 0
# new parameters related to gaussian filename distribution
rand_distr_type = file_access_dist.UNIFORM
rand_distr_type_str = 'uniform'
mean_index_velocity = 0.0  # default is a fixed mean for the distribution
gaussian_stddev = 1000.0  # just a guess, means most of accesses within 1000 files?
# just a guess, most files will be created before they are read
create_stddevs_ahead = 3.0
drift_time = -1
pause_file = '/var/tmp/pause'
compression_ratio = 0.0
direct = False
prefix = 'f'
rawdevice = ''
randommap = False
fill = False
dedupe_percentage = 0
threads = 1

def parseopts(argv):
    global top_directory, starting_gun_file, opcount, max_files, file_size, duration
    global blocksize, rsptimes, bw
    global fsync_probability_pct, fdatasync_probability_pct, workload_table_filename
    global stats_report_interval, levels, dirs_per_level
    global rand_distr_type, rand_distr_type_str, mean_index_velocity, gaussian_stddev, create_stddevs_ahead
    global compression_ratio, direct, prefix, rawdevice, randommap, fill, dedupe_percentage, threads

    if len(argv) % 2 != 1:
        usage('all options must have a value')
    try:
        ix = 1
        while ix < len(argv):

            nm = argv[ix]
            val = argv[ix+1]
            ix += 2
            if nm == '--help' or nm == '-h':
                usage()
            elif nm == '--starting-gun-file' or nm == '-S':
                starting_gun_file = os.path.join(top_directory, val)
            elif nm == '--top-directory' or nm == '-t':
                top_directory = val
            elif nm == '--workload-table' or nm == '-w':
                workload_table_filename = val
            elif nm == '--operation-count' or nm == '-o':
                opcount = int(val)
            elif nm == '--duration' or nm == '-d':
                duration = int(val)
            elif nm == '--max-files' or nm == '-f':
                max_files = int(val)
            elif nm == '--file-size' or nm == '-s':
                if ':' in val:
                    file_size = (int(val.split(':')[0]), int(val.split(':')[1]))
                else:
                    file_size = int(val)
            elif nm == '--blocksize' or nm == '-b':
                if ':' in val:
                    blocksize = (int(val.split(':')[0]), int(val.split(':')[1]))
                else:
                    blocksize = int(val)
            elif nm == '--fdatasync' or nm == '-y':
                fdatasync_probability_pct = int(val)
            elif nm == '--fsync' or nm == '-Y':
                fsync_probability_pct = int(val)
            elif nm == '--levels' or nm == '-l':
                levels = int(val)
            elif nm == '--dirs-per-level' or nm == '-D':
                dirs_per_level = int(val)
            elif nm == '--short-stats' or nm == '-a':
                short_stats = True
            elif nm == '--report-interval' or nm == '-i':
                stats_report_interval = int(val)
            elif nm == '--response-times' or nm == '-T':
                rsptimes = val
            elif nm == '--bandwidth' or nm == '-b':
                bw = val
            elif nm == '--random-distribution' or nm == '-+D':
                v = val.lower()
                if v == 'uniform':
                    rand_distr_type = file_access_dist.UNIFORM
                elif v == 'gaussian':
                    rand_distr_type = file_access_dist.GAUSSIAN
                else:
                    usage('random distribution must be "uniform" or "gaussian"')
                rand_distr_type_str = v
            elif nm == '--mean-velocity' or nm == '-+v':
                mean_index_velocity = float(val)
            elif nm == '--gaussian-stddev' or nm == '-+d':
                gaussian_stddev = float(val)
            elif nm == '--create_stddevs-ahead' or nm == '-+c':
                create_stddevs_ahead = float(val)
            elif nm == '--compression-ratio' or nm == '-c':
                compression_ratio = float(val)                
            elif nm == '--pause_file' or nm == '-p':
                pause_file = val
            elif nm == '--direct' or nm == '-+d':
                direct = True
            elif nm == '--prefix' or nm == '-P':
                prefix = val
            elif nm == '--rawdevice' or nm == '-+r':
                rawdevice = val
            elif nm == '--randommap' or nm == '-+R':
                randommap = True
            elif nm == '--fill' or nm == '-F':
                fill = True
            elif nm == '--dedupe-percentage' or nm == '-+D':
                dedupe_percentage = int(val)
            elif nm == '--threads' or nm == '-+t':
                threads = int(val)
            else:
                usage('syntax error for option %s value %s' % (nm, val))
    except Exception as e:
        usage(str(e))
    print('')
    print((
        '%9s = top directory\n'
        '%9s = starting gun file\n'
        '%20s%9d = operation count\n'
        '%20s%9d = duration\n'
        '%20s%9d = maximum files\n'
        '%17s%1s = file size (KB)\n'
        '%11s%9s = block size (KB)\n'
        '%11s%9d = fdatasync percentage\n'
        '%11s%9d = fsync percentage\n'
        '%11s%9d = directory levels\n'
        '%11s%9d = directories per level\n'
        '%20s = filename random distribution\n'
        '%11s%9.1f = mean index velocity\n'
        '%11s%9.1f = gaussian stddev\n'
        '%11s%9.1f = create stddevs ahead\n'
        '%20s = save response times\n'
        '%20s = save bandwidth\n'
        '%11s%9.1f = compression ratio\n'
        '%11s%9d = directIO\n'
        '%20s = prefix\n'
        '%20s = rawdevice\n'
        '%20s = random map\n'
        '%20s = fill device\n'
        '%20s = dedupe_percentage\n'
        '%20s = threads\n'
        % (top_directory, starting_gun_file, '', opcount, '', duration, '', max_files, '', str(file_size), '', str(blocksize),
           '', fdatasync_probability_pct, '', fsync_probability_pct,
           '', levels, '', dirs_per_level,
           rand_distr_type_str, '', mean_index_velocity, '', gaussian_stddev, '', create_stddevs_ahead,
           str(rsptimes), str(bw), '', compression_ratio, '', direct, prefix, rawdevice, randommap, fill, str(dedupe_percentage), str(threads))))


         
    if workload_table_filename != None:
        print('%20s = workload table filename' % workload_table_filename)
    if stats_report_interval > 0:
        print('%11s%9d = statistics report intervalpercentage' %
              ('', stats_report_interval))
    if (duration == 1):
        print('do "python fs-drift.py --help" for list of command line parameters')
    sys.stdout.flush()




if __name__ == "__main__":
    parseopts(sys.argv)
