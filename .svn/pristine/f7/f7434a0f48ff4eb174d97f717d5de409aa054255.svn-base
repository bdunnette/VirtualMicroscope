#!/usr/bin/env python

# William Holloway william.holloway@nyumc.org
#
# Copyright (C) 2008-2009 NYU Langone Medical Center
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.-

import os
import sys
from tiftiler import *


def process_svs(file, out_dir, base_dir):
    valid_exts = ['.svs', '.SVS']
    #validate input file
    if os.path.splitext(file)[1] not in valid_exts:
        raise Exception, 'File ' + file + ' is not an Aperio SVS image file.'

    svs_file = os.path.split(file)[1]
    clean_name = clean_up_name(svs_file.split('.')[0])
    out_dir = os.path.join(out_dir, clean_name)
    gen_dir(out_dir)
    os.chdir(out_dir)

    os.system('tiffsplit ' + file)
    os.rename('xaaa.tif', 'tmp.tif')
    os.system('rm x*.tif')

    tmp_file = os.path.join(out_dir, 'tmp.tif')
    tile(tmp_file, out_dir, True)


# Main processing
if __name__ == '__main__':
    from optparse import OptionParser
    usage = '''
    usage:
		%prog [--dir dir] [--outdir outdir]

    examples:
		%prog --dir /path/to/dir/with/svs/files
			=> Generate tiles from all svs files in /path/to/dir/with/svs/files

            '''
    parser = OptionParser(usage=usage)

    parser.add_option('--dir', default='', dest='dir',
                      help='The full or relative path to a directory '\
                      'containing one or more svs files to tile.')

    parser.add_option('--outdir', default='./aperio_output', dest='outdir',
                      help=('The full or relative path to the directory '
                      'which will serve as the parent directory '
                      'for all processed tiled image directories.'))

    (options, args) = parser.parse_args(sys.argv)

    if not options.dir:
        parser.error('The option --dir must be specified. ')

    try:
        base_dir = os.path.abspath(os.curdir)
        src_dir = os.path.abspath(os.path.normcase(options.dir))
        out_dir = os.path.abspath(os.path.normcase(options.outdir))
        print ('No output directory specified. Using default directory: ' + out_dir)
        for file in os.listdir(src_dir):
            print 'Processing: ' + file
           file = os.path.join(src_dir, file)
           process_svs(file, out_dir, base_dir)
    except Exception, e:
        print 'Could not process images in %s: %s' % (options.dir, str(e))

    sys.exit(0)
