# random_buffer.py - generate a random but printable text string

import string
import array
import shlex
import opts
import os
import random
from common import fsdrift_directory
from subprocess import Popen, PIPE, call

seeds = [int.from_bytes(os.urandom(6), 'big')]

def get_seed():
    global seeds
    p = random.randint(0,100)
    if p > opts.dedupe_percentage:
        seed = int.from_bytes(os.urandom(6), 'big')
        seeds.append(seed)
    if p <= opts.dedupe_percentage:
        seed = random.choice(seeds)
    return seed

def get_lz_data(params):
    args = shlex.split(params)
    proc = Popen([fsdrift_directory+'/lzdatagen/lzdgen'] +
                 args, stdout=PIPE, stderr=PIPE)
    out, error = proc.communicate()

    if error:
        print(error)
    return out

def gen_buffer( size_bytes ):
    if opts.compression_ratio == 0.0:
       b = array.array('B')
       for k in range(0, size_bytes):
               index = k % len(string.printable)
               printable_char = string.printable[index]
               b.append(ord(printable_char))
       return b
    else:
        if size_bytes == 0:
            return ''
        params = '-r ' + str(opts.compression_ratio) + ' -s ' + str(size_bytes) + ' -S ' + str(get_seed()) +' -'
        data = get_lz_data(params)
        return data
        


if __name__ == '__main__':
    print(gen_buffer(100))

