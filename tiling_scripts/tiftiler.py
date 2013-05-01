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

import re
import os
import subprocess
import math


def clean_up_name(arg):
    arg = re.sub('\W', '_', arg)
    arg = re.sub('_+', '_', arg)
    arg = re.sub('_$', '', arg)
    arg = re.sub('^_', '', arg)
    return arg


def gen_dir(dir):
    norm = os.path.normcase(dir)
    if not os.path.exists(norm):
        os.makedirs(norm)


def get_x_dim(file):
    proc = subprocess.Popen('vips im_header_int Xsize ' + file,
                            shell=True, stdout=subprocess.PIPE)
    return int(proc.communicate()[0].strip())


def get_y_dim(file):
    proc = subprocess.Popen('vips im_header_int Ysize ' + file,
                            shell=True, stdout=subprocess.PIPE)
    return int(proc.communicate()[0].strip())


def known_codec(tif_file):
    cmd = ('tiffinfo %s | grep "Compression Scheme" | grep -v 3300 | wc -l'
           % tif_file)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return int(proc.communicate()[0].strip())


def uncompress_tif(tif_file, out_dir):
    import openslide
    tmp_file = os.path.join(out_dir, 'os_tmp.tif')
    os_image = openslide.Openslide(tif_file)
    dims = os_image.getSize(0)
    x_pixels = dims[0]
    y_pixels = dims[1]
    os_tmp = os_image.getImageRGB(0, 0, 0, x_pixels, y_pixels)
    os_tmp.save(tmp_file)
    os.rename(tmp_file, tif_file)


def convert_to_vips(tif_file, out_dir):
    vips_file = os.path.join(out_dir, 'tmp.v')
    cmd = 'vips im_tiff2vips %s %s 2>/dev/null' % (tif_file, vips_file)
    proc = subprocess.Popen(cmd, shell=True)
    status = os.waitpid(proc.pid, 0)
    os.unlink(tif_file)
    return vips_file


def is_blank_tile(tile_file):
    cmd = ('identify -verbose %s | grep "65536: " | grep "black" | wc -l'
           % tile_file)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return int(proc.communicate()[0].strip())


def tile(tif_file, out_dir, remove_blank_tiles=0, verbose=0):

    if bool(verbose):
        print 'tiliing image ' + tif_file

    if not known_codec(tif_file):
        if verbose:
            print 'uncompressing image'
        uncompress_tif(tif_file, out_dir)

    vips_file = convert_to_vips(tif_file, out_dir)

    tmp_file = os.path.join(out_dir, 'tmp-file.v')
    tile_dim = 256

    source_x_pix = get_x_dim(vips_file)
    source_y_pix = get_y_dim(vips_file)

    if source_y_pix > source_x_pix:
        if bool(verbose):
            print 'rotating image...'
        cmd = 'vips im_rot90 %s %s' % (vips_file, tmp_file)
        os.system(cmd)
        os.rename(tmp_file, vips_file)
        temp = source_x_pix
        source_x_pix = source_y_pix
        source_y_pix = temp

    source_x_tiles = int(math.ceil(source_x_pix / float(tile_dim)))
    source_y_tiles = int(math.ceil(source_y_pix / float(tile_dim)))

    max_zoom = int(math.ceil(math.log(source_x_tiles, 2)))
    max_x_edge_tile = int(math.pow(2, max_zoom))

    max_y_edge_log = int(math.ceil(math.log(source_y_tiles, 2)))
    max_y_edge_tile = int(math.pow(2, max_y_edge_log))

    delta = max_x_edge_tile - max_y_edge_tile

    max_x_edge_pix = max_x_edge_tile * tile_dim
    max_y_edge_pix = max_y_edge_tile * tile_dim

    x_pad = (max_x_edge_pix - source_x_pix) / 2
    y_pad = (max_y_edge_pix - source_y_pix) / 2

    cmd = ('vips im_embed %s %s %s %s %s %s %s'
           % (vips_file, tmp_file, 0, x_pad, y_pad,
              max_x_edge_pix, max_y_edge_pix))

    resize = subprocess.Popen(cmd, shell=True)
    sts = os.waitpid(resize.pid, 0)
    os.rename(tmp_file, vips_file)

    if source_x_tiles % 2 != 0:
        source_x_tiles = source_x_tiles + 1
    if source_y_tiles % 2 != 0:
        source_y_tiles = source_y_tiles + 1

    x_offset = (max_x_edge_tile - source_x_tiles) / 2
    y_offset = (max_x_edge_tile - source_y_tiles) / 2
    y_delta = delta / 2

    for zoom in range(max_zoom, -1, -1):
        if bool(verbose):
            print 'Processing zoom level ' + str(zoom)
        tiles = int(math.pow(2, zoom))
        #resize image
        if zoom < max_zoom:
            cmd = 'vips im_shrink ' + vips_file + ' ' + tmp_file + ' 2 2'
            resize = subprocess.Popen(cmd, shell=True)
            sts = os.waitpid(resize.pid, 0)
            os.rename(tmp_file, vips_file)

        x_dim = get_x_dim(vips_file) / tile_dim
        y_dim = get_y_dim(vips_file) / tile_dim

        num_x_tiles = tiles - 2 * x_offset
        num_y_tiles = tiles - 2 * y_offset

        if x_dim != y_dim and y_dim <= num_y_tiles:
            #square up the image
            y_pad = ((x_dim - y_dim) / 2) * tile_dim
            dim = x_dim * tile_dim
            cmd = 'vips im_embed %s %s %s %s %s %s %s' % (vips_file, tmp_file, 0, 0, y_pad, dim, dim)
            resize = subprocess.Popen(cmd, shell=True)
            sts = os.waitpid(resize.pid, 0)
            os.rename(tmp_file, vips_file)
            y_delta = 0

        for y in range(y_offset, tiles - y_offset):
            for x in range(x_offset, tiles - x_offset):
                left = x * tile_dim
                if y > y_delta:
                    top = (y - y_delta) * tile_dim
                else:
                    top = y * tile_dim
                tile_name = 'tile_%s_%s_%s.jpg' % (zoom, x, y)
                tile_file = os.path.join(out_dir, tile_name)
                cmd = 'vips im_extract_area %s %s %s %s 256 256 2>/dev/null' % (vips_file, tile_file, left, top)
                extract = subprocess.Popen(cmd, shell=True)
                sts = os.waitpid(extract.pid, 0)
                if remove_blank_tiles and is_blank_tile(tile_file):
                    if bool(verbose):
                        print 'Removing tile %s ' % tile_file
                    os.unlink(tile_file)

        x_offset = x_offset / 2
        y_offset = y_offset / 2
        if y_delta > 0:
            y_delta = y_delta / 2
        if x_offset == 1:
            x_offset = 0
        if y_offset == 1:
            y_offset = 0
        if y_delta == 1:
            y_delta = 0
    os.unlink(vips_file)
    if bool(verbose):
        print 'done'
