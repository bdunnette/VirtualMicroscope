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
# THE SOFTWARE.

import sys
import os
import re
import subprocess
from tiftiler import *


def stitch_me(bacus_dir, out_dir, zlevel):

    clean_name = clean_up_name(os.path.basename(bacus_dir))
    out_dir = os.path.join(out_dir, clean_name)
    gen_dir(out_dir)
    datafile = os.path.join(out_dir, clean_name + '.dat')
    tiffile = os.path.join(out_dir, clean_name + '.tif')
    canvas = os.path.join(out_dir, 'canvas.jpg')
    tmpfile = os.path.join(out_dir, 'tmp.v')
    tmpfile2 = os.path.join(out_dir, 'tmp2.v')
    tmptilefile = os.path.join(out_dir, 'tile.v')

    if zlevel == 'all':
        zall = ['u3','u2','u1','0','d1','d2','d3']
    else:
        zall = [zlevel]

    for zval in zall:
        parse_ini_file(bacus_dir, datafile, zval)
        #make canvas
        tile_data = []
        img_data = open(datafile, 'r')
        for line in img_data:
            tile_data.append(line.strip())

        xdim = tile_data[0].split('x')[0]
        ydim = tile_data[0].split('x')[1]

        #make a little white vips file
        cmd = 'convert -size %sx%s -depth 8 pattern:GRAY100 -type TrueColor %s' % (1, 1, canvas)
        os.system(cmd)
        cmd = 'vips im_jpeg2vips %s %s' % (canvas, tmpfile)
        os.system(cmd)
        os.unlink(canvas)
        #resize vips canvas
        cmd = 'vips im_embed %s %s %s %s %s %s %s' % (tmpfile, tmpfile2,
                                                      4, 0, 0, xdim, ydim)
        os.system(cmd)
        os.rename(tmpfile2, tmpfile)

        for i in range(1, len(tile_data)):
            details = tile_data[i].split('|')
            cmd = 'vips im_jpeg2vips "%s" %s' % (details[0], tmptilefile)
            os.system(cmd)
            cmd = 'vips im_insertplace %s "%s" %s %s' % (tmpfile, tmptilefile, details[1], details[2])
            os.system(cmd)

        os.unlink(tmptilefile)
        os.unlink(datafile)
        #convert to tiff
        cmd = 'vips im_vips2tiff %s %s' % (tmpfile, tiffile)
        os.system(cmd)
        os.unlink(tmpfile)
        #tile it
        print 'tiling image...'
        tile(tiffile, out_dir, zval)


def parse_ini_file(bacus_dir, datafile, zlevel):
    numtiles = 0
    steartX = 0
    steartY = 0
    XStepSize = 0
    YStepSize = 0
    tile_ext = ''

    maxX = 0
    minY = sys.maxint
    xDim = 0
    yDim = 0

    if str(zlevel) == '0':
        zlevel = ''
    else:
        zlevel = '_' + zlevel

    ini_file = os.path.join(bacus_dir, 'FinalScan.ini')
    ini_data = open(ini_file, 'r')

    img_data = open(datafile, 'w')
    image_data = []

    try:
        for line in ini_data:
            if (re.search('^\[Da', line) or re.search('^x=', line) or
                    re.search('^y=', line)):
                image_data.append(line.strip())
            elif re.search('^\lAnalysisImageCount', line):
                numtiles = int(get_val(line))
            elif re.search('^lXStepSize', line):
                XStepSize = int(get_val(line))
            elif re.search('^lYStepSize', line):
                YStepSize = int(get_val(line))
            elif re.search('^tImageType', line):
                tile_ext = get_val(line)
    finally:
        ini_data.close()

    for i in range(0, len(image_data), 3):
        X = int(get_val(image_data[i + 1]))
        Y = int(get_val(image_data[i + 2]))
        X = round(X / (XStepSize / 752.0))
        Y = round(Y / (YStepSize / 480.0)) * -1
        if X > maxX:
            maxX = X
        if Y < minY:
            minY = Y

    for i in range(0, len(image_data), 3):
        X = int(get_val(image_data[i + 1]))
        Y = int(get_val(image_data[i + 2]))
        X = round(X / (XStepSize / 752.0))
        tileX = int(maxX - X)
        Y = round(Y / (YStepSize / 480.0)) * -1
        tileY = Y - minY
        if tileX > xDim:
            xDim = int(tileX)
        if tileY > yDim:
            yDim = int(tileY)

    xDim += 752
    yDim += 480
    out = '%s x %s\n' % (xDim, yDim)
    img_data.write(out)

    for i in range(0, len(image_data), 3):
        tile = os.path.join(bacus_dir, image_data[i][1:-1:] + zlevel +
                            tile_ext)
        X = int(get_val(image_data[i + 1]))
        Y = int(get_val(image_data[i + 2]))
        tileX = int(maxX - round(X / (XStepSize / 752.0)))
        tileY = int(round(Y / (YStepSize / 480.0)) * -1 - minY)
        out = '%s|%s|%s\n' % (tile, tileX, tileY)
        img_data.write(out)

    img_data.close()


def get_val(pair):
    return pair.split('=')[1].strip()


# Main processing
if __name__ == '__main__':
    from optparse import OptionParser
    usage = '''
    usage:
        %prog [--dir dir] [--outdir outdir]

    examples:
        %prog --dir /path/to/bacus_images
                => Reconstruct and tile images in bacus_images directory

            '''
    parser = OptionParser(usage=usage)
    parser.add_option('--dir', default='', dest='dir',
                      help='The full or relative path to top level directory '\
                      'containing Bacus image directories.')

    parser.add_option('--outdir', default='./bacus_output', dest='outdir',
                      help='The full or relative path to the directory '\
                      'which will serve as the parent directory for '\
                      'all processed images.')

    parser.add_option('--zlevel', default='0', dest='zlevel',
                      help='The z level to use. Default is 0. '\
                      'Valid options are u3-u1, 0, d1-d3 or all. '\
                      'If "all", all z levels will be tiled!')

    (options, args) = parser.parse_args(sys.argv)

    if not options.dir:
        parser.error('The option --dir must be specified. ')

    #try:
    base_dir = os.path.abspath(os.curdir)
    src_dir = os.path.abspath(os.path.normcase(options.dir))
    out_dir = os.path.abspath(os.path.normcase(options.outdir))
    print 'Processed files will be output to: ' + out_dir
    for d in os.listdir(src_dir):
        d = os.path.join(src_dir, d)
        if os.path.isdir(d):
            print 'Processing: ' + d
            stitch_me(d, out_dir, options.zlevel)

    #except Exception, e:
    #    print 'Could not process images in %s: %s' % (options.dir, str(e))

    sys.exit(0)
