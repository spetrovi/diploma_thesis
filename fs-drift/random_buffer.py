# random_buffer.py - generate a random but printable text string

import string
import array
import shlex
import opts
import os
import random
from common import fsdrift_directory
from subprocess import Popen, PIPE, call

def gen_4k_block():
    bytes_per_4k_block = 4096
    random_bytes = int((1/opts.compression_ratio) * bytes_per_4k_block)
    return bytearray(os.urandom(random_bytes)) + bytearray((bytes_per_4k_block-random_bytes)*b'\0')

def gen_compressible_buffer(size):
    to_dedupe = (opts.dedupe_percentage/100)
    if not to_dedupe:
        to_dedupe = 1
        repeat_buf = 1
    else:
        repeat_buf = int(1 / (1 - to_dedupe))
    number_of_blocks = int((size / 4096) * to_dedupe)

    blocks = bytearray()
    for i in range(number_of_blocks):
        blocks += gen_4k_block()
    
    buf = bytearray()
    for i in range(repeat_buf):
        buf += blocks
    return buf

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
        
        return gen_compressible_buffer(size_bytes)
        


if __name__ == '__main__':
    print(gen_buffer(100))

