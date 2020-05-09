# fsop.py - module containing filesystem operation types and common code for them

# NOTE: this version requires "numpy" rpm to be installed
# std python modules
import os
import os.path
import random
import errno
import time
import random_buffer
# my modules
import common
from common import rq, file_access_dist, verbosity, OK, NOTOK, BYTES_PER_KB, FD_UNDEFINED
import opts
import numpy  # for gaussian distribution
import subprocess
import mmap
import struct
from fcntl import ioctl


# operation counters, incremented by op function below
have_created = 0
have_deleted = 0
have_linked = 0
have_written = 0
have_appended = 0
have_randomly_written = 0
have_read = 0
have_randomly_read = 0
have_renamed = 0
have_truncated = 0
have_hlinked = 0
have_discarded = 0

# throughput counters
read_requests = 0
read_bytes = 0
randread_requests = 0
randread_bytes = 0
write_requests = 0
write_bytes = 0
randwrite_requests = 0
randwrite_bytes = 0
fsyncs = 0
fdatasyncs = 0
dirs_created = 0
discard_bytes = 0
discard_requests = 0

# time counters
time_before = 0
time_after = 0
precise_time = 0

# error counters
e_already_exists = 0
e_file_not_found = 0
e_no_dir_space = 0
e_no_inode_space = 0
e_no_space = 0

# most recent center
last_center = 0

#offsets
read_offset = 0
write_offset = 0

#We will generate and shuffle list of all posible block offsets on a device
offset_list = []
offsets_written = []

# someday these two should be parameters
total_dirs = 1

link_suffix = '.s'
hlink_suffix = '.h'
rename_suffix = '.r'

buf = None

large_prime = 12373

# for gaussian distribution with moving mean, we need to remember simulated time
# so we can pick up where we left off with moving mean

simtime_pathname = '/var/tmp/fs-drift-simtime.tmp'
SIMULATED_TIME_UNDEFINED = None
simulated_time = SIMULATED_TIME_UNDEFINED  # initialized later
time_save_rate = 5

class Result(object):
    def __init__(self, success, errors, name, time_before = 0, time_after = 0, precise_time = 0, size = 0):
        self.success = success
        self.time_before = time_before
        self.time_after = time_after
        self.precise_time = precise_time
        self.name = name
        self.size = size
        self.errors = errors      


              
#Randommap creates a ranodmised list of all possible offsets given the record size
def randommap():
    global offset_list
    fd = os.open(opts.rawdevice, os.O_RDONLY)
    st_size = os.lseek(fd, 0, os.SEEK_END)
    os.close(fd)
    offset_list = [i for i in range(st_size//get_recsz())]
    random.shuffle(offset_list)



def scallerr(msg, fn, syscall_exception):
    err = str(syscall_exception.errno)
    print('ERROR: %s: %s syscall errno %s' % ( msg, fn, err))


def gen_random_dirname(file_index):
    d = opts.top_directory
    # multiply file_index ( < opts.max_files) by large number relatively prime to dirs_per_level
    index = file_index * large_prime
    for j in range(0, opts.levels):
        subdir_index = 1 + (index % opts.dirs_per_level)
        dname = 'd%04d' % subdir_index
        d = os.path.join(d, dname)
        index /= opts.dirs_per_level
    return d

#Generate file name for IO operation in accoradnce to dir tree and chosen random distribution
#If in rawdevice mode, return name of the device
def gen_random_fn(is_create=False):
    global total_dirs
    global simulated_time
    global last_center
    if opts.rawdevice:
        return opts.rawdevice
    if total_dirs == 1:  # if first time
        for i in range(0, opts.levels):
            total_dirs *= opts.dirs_per_level
    max_files_per_dir = opts.max_files // total_dirs

    if opts.rand_distr_type == file_access_dist.UNIFORM:
        # lower limit 0 means at least 1 file/dir
        index = random.randint(0, max_files_per_dir)
    elif opts.rand_distr_type == file_access_dist.GAUSSIAN:

        # if simulated time is not defined,
        # attempt to read it in from a file, set to zero if no file

        if simulated_time == SIMULATED_TIME_UNDEFINED:
            try:
                with open(simtime_pathname, 'r') as readtime_fd:
                    simulated_time = int(readtime_fd.readline().strip())
            except IOError as e:
                if e.errno != errno.ENOENT:
                    raise e
                simulated_time = 0
            print(('resuming with simulated time %d' % simulated_time))

        # for creates, use greater time, so that reads, etc. will "follow" creates most of the time
        # mean and std deviation define gaussian distribution

        center = (simulated_time * opts.mean_index_velocity)
        if is_create:
            center += (opts.create_stddevs_ahead * opts.gaussian_stddev)
        if verbosity & 0x20:
            print('%f = center' % center)
        index_float = numpy.random.normal(
            loc=center, scale=opts.gaussian_stddev)
        file_opstr = 'read'
        if is_create:
            file_opstr = 'create'
        if verbosity & 0x20:
            print('%s gaussian value is %f' % (file_opstr, index_float))
        #index = int(index_float) % max_files_per_dir
        index = int(index_float) % opts.max_files
        last_center = center

        # since this is a time-varying distribution, record the time every so often
        # so we can pick up where we left off

        if opts.drift_time == -1:
            simulated_time += 1
        if simulated_time % time_save_rate == 0:
            with open(simtime_pathname, 'w') as time_fd:
                time_fd.write('%10d' % simulated_time)

    else:
        index = 'invalid-distribution-type'  # should never happen
    if verbosity & 0x20:
        print('next file index %u out of %u' % (index, max_files_per_dir))
    dirpath = gen_random_dirname(index)
    fn = os.path.join(dirpath, opts.prefix + '%09d' % index)
    if verbosity & 0x20:
        print('next pathname %s' % fn)
    return fn

#Returns file size in bytes between 0 and max file size.
#If using direct IO, make it multiple of 4096 for memory alignment
def random_file_size():
    #In case user inputs range, do random file size
    if isinstance(opts.file_size, tuple):
        fsz = random.randint(opts.file_size[0] * BYTES_PER_KB, opts.file_size[1] * BYTES_PER_KB)
    else:
        fsz = opts.file_size * BYTES_PER_KB

    #if using directIO, align memory
    if opts.direct:
        fsz = int(fsz/4096)*4096
        if fsz == 0: fsz = 4096
    return fsz





#Return random offset for file size
#If using directIO, make it multiple of 4096 for memory alignemnt
def random_seek_offset(filesz):
    if opts.randommap:
        global offset_list
        if not offset_list: randommap()
#        random_index = random.randint(0, len(offset_list))
#        offset = offset_list[random_index]
        offset = offset_list.pop()
        return get_recsz()*offset

    if filesz < 0:
        return 0
    if opts.direct:
        offset = random.randint(0, int((filesz)/4096))*4096
#        offsets_written.append(offset)
        return offset
    else:
        return random.randint(0, filesz)


def try_to_close(closefd, fn):
    if closefd != FD_UNDEFINED:
        try:
            os.close(closefd)
        except OSError as e:
            scallerr('close', fn, e)
            return False
    return True

def get_recsz():
    if isinstance(opts.blocksize, tuple):
        recsz = random.randint(opts.blocksize[0] * BYTES_PER_KB, opts.blocksize[1] * BYTES_PER_KB)
    else:
        recsz = opts.blocksize * BYTES_PER_KB
    if opts.direct:
        return (recsz // 4096) * 4096
    return recsz

        

#Call fsync or fdatasync in accordance to input percentage chance
def maybe_fsync(fd):
    global fsyncs, fdatasyncs
    percent = random.randint(0, 100)
    if percent > opts.fsync_probability_pct + opts.fdatasync_probability_pct:
        return
    if percent > opts.fsync_probability_pct:
        fdatasyncs += 1
        os.fdatasync(fd)
    else:
        fsyncs += 1
        os.fsync(fd)

#Sequential read of file or block device
#In case of rawdevice, we remember the last read position and continue there
def read():
    global e_file_not_found, have_read, read_requests, read_bytes
    global time_before, time_after
    global precise_time
    global read_offset

    s = OK
    fd = FD_UNDEFINED
    fn = gen_random_fn()
    try:
        fd = os.open(fn, os.O_RDONLY | os.O_DIRECT * opts.direct)
        f = os.fdopen(fd, 'rb', 0)
        stinfo = os.fstat(fd)
        st_size = stinfo.st_size
        target_sz = random_file_size()
        #If using rawdevice, get its size by seeking the end of the device
        #Afterwards, seek to the last read position, to asure continuous reading
        if opts.rawdevice:
            st_size = os.lseek(fd, 0, os.SEEK_END)
            os.lseek(fd, read_offset, 0)
            read_offset += target_sz
            if read_offset > st_size:
                read_offset = 0
                os.lseek(fd, 0, os.SEEK_SET)

        if verbosity & 0x4000:
            print('read file %s sz %u' % (fn, st_size))
        total_read = 0        
        time_before = time.perf_counter()
        precise_time = 0
        while total_read < target_sz:
            recsz = get_recsz()

            #using mmap for correct memory alignment
            bytebuf = mmap.mmap(-1, recsz)

            #actual perf measurement
            start = time.perf_counter()
            count = f.readinto(bytebuf)
            end = time.perf_counter()

            precise_time += float(end - start)
            read_requests += 1
            read_bytes += count
            total_read += count

            if verbosity & 0x4000:
                print('seq. read off %u sz %u got %u' %\
                     (total_read, rdsz, count))
                print(time.perf_counter())

        time_after = time.perf_counter()
        if verbosity & 0x4000:
            print('read file %s sz %u' % (fn, st_size))
            print(time_before, time_after)
            print('finished seq. read of %u KB with bw %u KB/s' %\
                 (total_read/BYTES_PER_KB, (total_read/BYTES_PER_KB / float(time_after-time_before))))
        
        have_read += 1
    except os.error as e:
        if e.errno == errno.ENOENT:
            e_file_not_found += 1
        else:
            scallerr('close', fn, e)
            s = NOTOK
    try_to_close(fd, fn)
    return s


#Random read of file or rawdevice
def random_read():
    global e_file_not_found, have_randomly_read, randread_requests, randread_bytes
    global time_before, time_after
    global precise_time

    s = OK
    fd = FD_UNDEFINED
    fn = gen_random_fn()
    try:
        fd = os.open(fn, os.O_RDONLY | os.O_DIRECT * opts.direct)
        f = os.fdopen(fd, 'rb', 0)
        stinfo = os.fstat(fd)
        st_size = stinfo.st_size

        #If rawdevice, get it's size by seeking the end
        if opts.rawdevice:
            st_size = os.lseek(fd, 0, os.SEEK_END)

        if verbosity & 0x2000:
            print('randread %s filesize %u reqs' % (
                fn, st_size))
        total_count = 0
        target_sz = random_file_size()
        time_before = time.perf_counter()
        precise_time = 0
        while total_count < target_sz:
            recsz = get_recsz()

            #using mmap for memory alignment
            bytebuf = mmap.mmap(-1, recsz)
            off = os.lseek(fd, random_seek_offset(st_size-recsz), 0)            

            if verbosity & 0x2000:
                print('randread off %u sz %u' % (off, target_sz))

            #actual measurement
            start = time.perf_counter()
            count = f.readinto(bytebuf)
            end = time.perf_counter()

            precise_time += float(end - start)
            assert count > 0
            if verbosity & 0x2000:
                print('randread recsz %u count %u' % (recsz, count))
            total_count += count
            randread_bytes += count

            randread_requests += 1
        time_after = time.perf_counter()
        if verbosity & 0x2000:
            print('finished random. read of %u KB with bw %u KB/s' %\
                 (total_count/BYTES_PER_KB, (total_count/BYTES_PER_KB / float(time_after-time_before))))
        have_randomly_read += 1
    except os.error as e:
        if e.errno == errno.ENOENT:
            e_file_not_found += 1
        else:
            scallerr('random_read', fn, e)
            s = NOTOK
    try_to_close(fd, fn)
    return s


#Create a  new file
def create():
    global have_created, e_already_exists, write_requests, write_bytes, dirs_created
    global e_no_dir_space, e_no_inode_space, e_no_space
    global time_before, time_after
    global precise_time
    s = OK
    fd = FD_UNDEFINED
    fn = gen_random_fn(is_create=True)
    target_sz = random_file_size()
    if verbosity & 0x1000:
        print('create %s sz %s' % (fn, target_sz))
    subdir = os.path.dirname(fn)
    if not os.path.isdir(subdir):
        try:
            os.makedirs(subdir)
        except OSError as e:
            if e.errno == errno.ENOSPC:
                e_no_dir_space += 1
                return OK
            scallerr('create', fn, e)
            return NOTOK
        dirs_created += 1
    try:
        fd = os.open(fn, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_DIRECT * opts.direct)
        buf = random_buffer.gen_buffer(target_sz)
        total_sz = 0
        offset = 0
        time_before = time.perf_counter()
        precise_time = 0
        while total_sz < target_sz:
            recsz = get_recsz()
            if recsz + total_sz > target_sz:
                recsz = target_sz - total_sz
            m = mmap.mmap(-1, recsz)
            m.write(buf[offset:offset+recsz])
            start = time.perf_counter()
            count = os.write(fd, m)
            end = time.perf_counter()
            offset += count
            precise_time += float(end - start)
            assert count > 0
            if verbosity & 0x1000:
                print('create sz %u written %u' % (recsz, count))
            total_sz += count
            write_requests += 1
            write_bytes += count
        maybe_fsync(fd)
        time_after = time.perf_counter()
        if verbosity & 0x1000:
            print('finished create of %u KB with bw %u KB/s' %\
                 (total_sz/BYTES_PER_KB, (total_sz/BYTES_PER_KB / float(time_after-time_before))))
        have_created += 1
    except os.error as e:
        if e.errno == errno.EEXIST:
            e_already_exists += 1
        elif e.errno == errno.ENOSPC:
            e_no_inode_space += 1
        else:
            scallerr('create', fn, e)
            s = NOTOK
    try_to_close(fd, fn)
    return s

#Sequentially append the file or write to rawdevice
#If using rawdevice, we remember the last written position 
def append():
    global have_appended, write_requests, write_bytes, e_file_not_found
    global e_no_space
    global time_before, time_after
    global precise_time
    global write_offset

    s = OK
    fn = gen_random_fn()
    target_sz = random_file_size()
    buf = random_buffer.gen_buffer(target_sz)
    if verbosity & 0x8000:
        print('append %s sz %s' % (fn, target_sz))
    fd = FD_UNDEFINED
    try:
        fd = os.open(fn, os.O_WRONLY | os.O_APPEND | os.O_DIRECT * opts.direct)
        #If rawdevice, get its size by seeking the end
        #Then, seek the last written position to continue the write
        if opts.rawdevice:
            st_size = os.lseek(fd, 0, os.SEEK_END)
            os.lseek(fd, write_offset, 0)
            write_offset += target_sz
            if write_offset > st_size:
                write_offset = 0
                os.lseek(fd, 0, os.SEEK_SET)
            
        total_appended = 0
        offset = 0
        time_before = time.perf_counter()
        precise_time = 0
        while total_appended < target_sz:
            recsz = get_recsz()
            if recsz + total_appended > target_sz:
                recsz = target_sz - total_appended
            assert recsz > 0
            m = mmap.mmap(-1, recsz)
            if verbosity & 0x8000:
                print('append rsz %u' % (recsz))
            m.write(buf[offset:offset+recsz])
            
            #Actual perf. measurement
            start = time.perf_counter()
            count = os.write(fd, m)
            end = time.perf_counter()
    
            offset += count
            precise_time += float(end - start)
            assert count > 0
            total_appended += count
            write_requests += 1
            write_bytes += count
            offset_list.pop()
            

        maybe_fsync(fd)
        time_after = time.perf_counter()
        if verbosity & 0x8000:
            print('finished append(seq write) of %u KB with bw %u KB/s' %\
                 (total_appended/BYTES_PER_KB, (total_appended/BYTES_PER_KB / float(time_after-time_before))))
        have_appended += 1
    except os.error as e:
        if e.errno == errno.ENOENT:
            e_file_not_found += 1
        elif e.errno == errno.ENOSPC:
            e_no_space += 1
        else:
            scallerr('append', fn, e)
            s = NOTOK
    try_to_close(fd, fn)
    return s

#Random write of a file or a device
def random_write():
    global have_randomly_written, randwrite_requests, randwrite_bytes, e_file_not_found
    global e_no_space

    s = OK
    fd = FD_UNDEFINED
    fn = gen_random_fn()
    try:
        fd = os.open(fn, os.O_WRONLY | os.O_DIRECT * opts.direct)
        stinfo = os.fstat(fd)
        st_size = stinfo.st_size
        #If rawdevice, get its size by seeking the end
        if opts.rawdevice:
            st_size = os.lseek(fd, 0, os.SEEK_END)

        target_sz = random_file_size()
        buf = random_buffer.gen_buffer(target_sz)
        if verbosity & 0x20000:
            print('randwrite %s file size %u KB, target size %u KB' % (fn, st_size/BYTES_PER_KB, target_sz/1024))
        total_count = 0
        buffer_offset = 0
        time_before = time.perf_counter()
        precise_time = 0
        while total_count < target_sz:
            recsz = get_recsz()
            off = os.lseek(fd, random_seek_offset(st_size-recsz), 0)
            if verbosity & 0x20000:
                print('randwrite off %u sz %u' % (off, recsz))
            m = mmap.mmap(-1, recsz)
            m.write(buf[buffer_offset:buffer_offset+recsz])
            start = time.perf_counter()
            count = os.write(fd, m)
            end = time.perf_counter()
            precise_time += float(end - start)
            if verbosity & 0x20000:
                print('randwrite count=%u recsz=%u' % (count, recsz))
                print('finished randwrite block with bw %u KB/s' % ( (recsz/BYTES_PER_KB) / float(end - start)))
            assert count > 0
            total_count += count
            buffer_offset += count
            randwrite_requests += 1
            randwrite_bytes += count
        maybe_fsync(fd)
        time_after = time.perf_counter()
        if verbosity & 0x20000:
            print('finished rand. write of %u KB with bw %u KB/s' %\
                 (total_count/BYTES_PER_KB, (total_count/BYTES_PER_KB / precise_time)))
        have_randomly_written += 1

    except os.error as e:
        if e.errno == errno.ENOENT:
            e_file_not_found += 1
        elif e.errno == errno.ENOSPC:
            e_no_space += 1
        else:
            scallerr('random write', fn, e)
        #(self, success, errors, name, time_before, time_after, precise_time, size):
        return Result(False, e, 'random_write')

    try_to_close(fd, fn)

    return Result(True, '', 'random_write',time_before, time_after, precise_time, total_count)


def truncate():
    global have_truncated, e_file_not_found
    global time_before, time_after
    fd = FD_UNDEFINED
    s = OK
    fn = gen_random_fn()
    if verbosity & 0x40000:
        print('truncate %s' % fn)
    try:
        new_file_size = random_file_size()/3
        time_before = time.perf_counter()
        fd = os.open(fn, os.O_RDWR)
        os.ftruncate(fd, new_file_size)
        time_after = time.perf_counter()
        have_truncated += 1
    except os.error as e:
        if e.errno == errno.ENOENT:
            e_file_not_found += 1
        else:
            scallerr('truncate', fn, e)
            s = NOTOK
    try_to_close(fd, fn)
    return s


def link():
    global have_linked, e_file_not_found, e_already_exists
    global time_before, time_after
    fn = gen_random_fn()
    fn2 = gen_random_fn() + link_suffix
    if verbosity & 0x10000:
        print('link to %s from %s' % (fn, fn2))
    if not os.path.isfile(fn):
        e_file_not_found += 1
        return OK
    try:
        time_before = time.perf_counter()
        rc = os.symlink(fn, fn2)
        time_after = time.perf_counter()
        have_linked += 1
    except os.error as e:
        if e.errno == errno.EEXIST:
            e_already_exists += 1
            return OK
        elif e.errno == errno.ENOENT:
            e_file_not_found += 1
            return OK
        scallerr('link', fn, e)
        return NOTOK
    return OK


def hlink():
    global have_hlinked, e_file_not_found, e_already_exists
    global time_before, time_after
    fn = gen_random_fn()
    fn2 = gen_random_fn() + hlink_suffix
    if verbosity & 0x10000:
        print('hard link to %s from %s' % (fn, fn2))
    if not os.path.isfile(fn):
        e_file_not_found += 1
        return OK
    try:
        time_before = time.perf_counter()
        rc = os.link(fn, fn2)
        time_after = time.perf_counter()
        have_hlinked += 1
    except os.error as e:
        if e.errno == errno.EEXIST:
            e_already_exists += 1
            return OK
        elif e.errno == errno.ENOENT:
            e_file_not_found += 1
            return OK
        scallerr('link', fn, e)
        return NOTOK
    return OK


def delete():
    global have_deleted, e_file_not_found
    global time_before, time_after
    fn = gen_random_fn()
    if verbosity & 0x20000:
        print('delete %s' % (fn))
    try:
        linkfn = fn + link_suffix
        time_before = time.perf_counter()
        if os.path.isfile(linkfn):
            if verbosity & 0x20000:
                print('delete soft link %s' % (linkfn))
            os.unlink(linkfn)
        hlinkfn = fn + hlink_suffix
        if os.path.isfile(hlinkfn):
            if verbosity & 0x20000:
                print('delete hard link %s' % (hlinkfn))
            os.unlink(hlinkfn)
        os.unlink(fn)
        time_after = time.perf_counter()
        have_deleted += 1
    except os.error as e:
        if e.errno == errno.ENOENT:
            e_file_not_found += 1
            return OK
        scallerr('delete', fn, e)
        return NOTOK
    return OK

def random_discard():
    global have_discarded, e_file_not_found
    global discard_bytes, discard_requests
    global time_before, time_after
    global precise_time

    discard_size = get_recsz()

    fn = gen_random_fn()
    
    target_sz = random_file_size()

    if verbosity & 0x20001:
        print('discard %u B on %s' % (target_sz, fn))
    try:
        fd = os.open(fn, os.O_WRONLY)
        if opts.rawdevice:
            st_size = os.lseek(fd, 0, os.SEEK_END)

        discarded = 0
        BLKDISCARD =  0x12 << (4*2) | 119 # command for iocrl
        time_before = time.perf_counter()
        precise_time = 0
        while discarded < target_sz:
            recsz = discard_size
            offset = random_seek_offset(st_size-recsz)
            if verbosity & 0x20001:
                print('discard rsz %u' % (recsz))
            args = struct.pack('QQ', offset, recsz)
            start = time.perf_counter()
#            subprocess.call('blkdiscard -o ' + str(offset) + ' -l ' + str(recsz) + ' ' + fn, shell=True)
#            subprocess.call('blkdiscard -p ' + str(recsz) + ' ' + fn, shell=True)
            ioctl(fd, BLKDISCARD, args, 0)
            end = time.perf_counter()

            precise_time += float(end - start)
            discarded += recsz
 #           discarded += 21474836480
            discard_requests += 1


        time_after = time.perf_counter()

        have_discarded += 1
        discard_bytes += discarded

    except os.error as e:
        if e.errno == errno.ENOENT:
            e_file_not_found += 1
            return OK
        scallerr('random discard', fn, e)
        return Result(False, e, 'random_discard')
    try_to_close(fd, fn)
    return Result(True, '', 'random_discard',time_before, time_after, precise_time, discarded)


def rename():
    global have_renamed, e_file_not_found
    global time_before, time_after
    fn = gen_random_fn()
    fn2 = gen_random_fn()
    if verbosity & 0x20000:
        print('rename %s to %s' % (fn, fn2))
    try:
        time_before = time.perf_counter()
        os.rename(fn, fn2)
        time_after = time.perf_counter()
        have_renamed += 1
    except os.error as e:
        if e.errno == errno.ENOENT:
            e_file_not_found += 1
            return OK
        scallerr('rename', fn, e)
        return NOTOK
    return OK


rq_map = \
    {rq.READ: (read, "read"),
     rq.RANDOM_READ: (random_read, "random_read"),
     rq.CREATE: (create, "create"),
     rq.RANDOM_WRITE: (random_write, "random_write"),
     rq.APPEND: (append, "append"),
     rq.LINK: (link, "link"),
     rq.DELETE: (delete, "delete"),
     rq.RENAME: (rename, "rename"),
     rq.TRUNCATE: (truncate, "truncate"),
     rq.HARDLINK: (hlink, "hardlink"),
     rq.RANDOM_DISCARD: (random_discard, "random_discard")
     }


if __name__ == "__main__":
    opts.parseopts()
    buckets = 20
    histogram = [0 for x in range(0, buckets)]
    with open('/tmp/filenames.list', 'w') as fns:
        for i in range(0, opts.opcount):
            fn = gen_random_fn()
            fns.write(fn + '\n')
            # print(fn)
            namelist = fn.split('/')
            fname = namelist[len(namelist)-1].split('.')[0]
            # print(fname)
            num = int(fname[1:])
            bucket = num*len(histogram)/opts.max_files
            histogram[bucket] += 1
    print(histogram)
    assert(sum(histogram) == opts.opcount)
