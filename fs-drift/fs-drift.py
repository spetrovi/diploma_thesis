#!/usr/bin/python3

# fs-drift.py - user runs this module to generate workload
# "-h" option generates online help

import os
import os.path
import time
import sys
import random
import event
import fsop
import common
from common import rq, OK, NOTOK, BYTES_PER_KB, fsdrift_directory
import opts
import errno
import subprocess
import threading

# get byte counters from fsop

start_time = 0
total_errors = 0

def refresh_counters():
    global counters
    counters = {'read': fsop.read_bytes, 'create': fsop.write_bytes, 'append': fsop.write_bytes,
                'random_write': fsop.randwrite_bytes, 'random_read': fsop.randread_bytes, 'random_discard': fsop.discard_bytes}

# instead of looking up before deletion, do reverse, delete and catch exception


def ensure_deleted(file_path):
    try:
        os.unlink(file_path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise e

# print out counters for the interval that just completed.


def print_short_stats():
    print('elapsed time: %9.1f' % (time.perf_counter() - start_time))
    print('\n'\
        '%9u = center\n' \
        '%9u = files created\t' \
        '%9u = files appended to\n' \
        '%9u = files random write\t' \
        '%9u = files read\n' \
        '%9u = files randomly read\n' \
        % (fsop.last_center, fsop.have_created, fsop.have_appended, fsop.have_randomly_written,
           fsop.have_read, fsop.have_randomly_read))
    sys.stdout.flush()


def print_stats():
    global start_time
    global total_errors
    print()
    print('elapsed time: %9.1f' % (time.perf_counter() - start_time))
    print('\n\n'\
        '%9u = center\n' \
        '%9u = files created\n' \
        '%9u = files appended to\n' \
        '%9u = files randomly written to\n' \
        '%9u = files read\n' \
        '%9u = files randomly read\n' \
        '%9u = files truncated\n' \
        '%9u = files deleted\n' \
        '%9u = files renamed\n' \
        '%9u = softlinks created\n' \
        '%9u = hardlinks created\n' \
        % (fsop.last_center, fsop.have_created, fsop.have_appended, fsop.have_randomly_written,
           fsop.have_read, fsop.have_randomly_read, fsop.have_truncated,
           fsop.have_deleted, fsop.have_renamed, fsop.have_linked, fsop.have_hlinked))

    print('%9u = read requests\n' \
        '%9u = read bytes\n'\
        '%9u = random read requests\n' \
        '%9u = random read bytes\n' \
        '%9u = write requests\n' \
        '%9u = write bytes\n'\
        '%9u = random write requests\n' \
        '%9u = random write bytes\n' \
        '%9u = fdatasync calls\n' \
        '%9u = fsync calls\n' \
        '%9u = leaf directories created\n' \
        '%9u = discard requests\n' \
        '%9u = discard bytes\n' \
        % (fsop.read_requests, fsop.read_bytes, fsop.randread_requests, fsop.randread_bytes,
           fsop.write_requests, fsop.write_bytes, fsop.randwrite_requests, fsop.randwrite_bytes,
           fsop.fdatasyncs, fsop.fsyncs, fsop.dirs_created, fsop.discard_requests, fsop.discard_bytes))

    print('%9u = no create -- file already existed\n'\
        '%9u = file not found\n'\
        % (fsop.e_already_exists, fsop.e_file_not_found))
    print('%9u = no directory space\n'\
        '%9u = no space for new inode\n'\
        '%9u = no space for write data\n'\
        % (fsop.e_no_dir_space, fsop.e_no_inode_space, fsop.e_no_space))
    print('%9u = total errors' % total_errors)
    sys.stdout.flush()


class fs_drift_instance(object):
    def __init__(self, num):
        self.num = num
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True                            # Daemonize thread
        self.thread.start()                                  # Start the execution

    def run(self):
        if opts.rsptimes:
            rsptime_filename = opts.rsptimes + '/fs-drift_%d_%d_%d_th_rspt.csv' % (int(time.perf_counter()), os.getpid(), self.num)
            rsptime_file = open(rsptime_filename, "w").close()


        if opts.bw:
            bw_filename = opts.bw + '/fs-drift_%d_%d_%d_th_bw.csv' % (int(time.perf_counter()), os.getpid(), self.num)
            bw_file = open(bw_filename, "w").close()


        if opts.starting_gun_file:
            while not os.access(opts.starting_gun_file, os.R_OK):
                time.sleep(1)

        event_count = 0
        op = 0
        while True:

            # every 1000 events, check for "stop file" that indicates test should end

            event_count += 1
            if (event_count % 1000 == 0) and os.access(stop_file, os.R_OK):
                break

            # if using device fullness to limit test
            if opts.fill and fsop.e_no_space:
                    break
                


            # if using operation count to limit test

            if opts.opcount > 0:
                if op >= opts.opcount:
                    break
                op += 1

            # if using duration to limit test

            if opts.duration > 0:
                elapsed = time.perf_counter() - start_time
                if elapsed > opts.duration:
                    break
            x = event.gen_event()
            (fn, name) = fsop.rq_map[x]
            if common.verbosity & 0x1:
                print()
                print(x, name)
            before_drift = time.perf_counter()

            try:
                result = fn()
                before = result.time_before
                total_time = result.precise_time
                if opts.rsptimes:
                    rsptime_file = open(rsptime_filename, "a+")
                    rsptime_file.write('%9.9f , %9.6f , %s\n' %
                                       (before - start_time,  total_time, result.name))
                    rsptime_file.close()

                if opts.bw:
                    bw_file = open(bw_filename, "a+")
                    total_size = result.size
                    if total_size > 0:
                        bw_file.write('%9.9f , %9.6f , %s\n' % (
                            before - start_time,  ((total_size/BYTES_PER_KB) / total_time), result.name))
                    bw_file.close()

            except KeyboardInterrupt as e:
                print("received SIGINT (control-C) signal, aborting...")
                break
            
            if not result.success:
                global total_errors
                total_errors += 1

            if (opts.drift_time > 0) and (before_drift - last_drift_time > opts.drift_time):
                fsop.simulated_time += opts.drift_time
                last_drift_time = before_drift

        if opts.rsptimes:
                rsptime_file.close()
                print('response time file is %s' % rsptime_filename)

        if opts.bw:
                bw_file.close()
                print('bandwidth file is %s' % bw_filename)

# the main program
def main(argv):
    
    opts.parseopts(argv)
    event.parse_weights()
    event.normalize_weights()



    global total_errors
    total_errors = 0


    try:
        os.mkdir(opts.top_directory)
    except os.error as e:
        if e.errno != errno.EEXIST:
            raise e


    sys.stdout.flush()

    last_stat_time = time.perf_counter()
    last_drift_time = time.perf_counter()
    stop_file = opts.top_directory + os.sep + 'stop-file'

    # we have to synchronize threads across multiple hosts somehow, we do this with a
    # file in a shared file system.

    if opts.randommap or opts.fill:
        fsop.randommap()

    global start_time
    start_time = time.perf_counter()

    instances = []
    for i in range(opts.threads):
        instances.append(fs_drift_instance(i))

    if opts.starting_gun_file:
        open(opts.starting_gun_file, 'a').close()

    working = True
    before = fsop.time_before
    while working:
        if (opts.stats_report_interval > 0) and (before - last_stat_time > opts.stats_report_interval):
            if opts.short_stats == True:
                print_short_stats()
            else:
                print_stats()

        working = False
        for i in instances:
            working = i.thread.isAlive() | working
        if working:
            time.sleep(opts.stats_report_interval)
        else:
             break


    print_stats()
    if opts.starting_gun_file:
        ensure_deleted(opts.starting_gun_file)
    ensure_deleted(stop_file)

if __name__ == "__main__":
    main(sys.argv)
