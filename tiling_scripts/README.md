Introduction
============

The SVS_tiler.py script is a python script which will convert digitized microscope slides from the [Aperio ScanScope Virtual Slide](http://openslide.org/formats/aperio/) (.SVS) format into 256x256 pixel jpeg tiles suitable for use within a [Google Maps API](http://code.google.com/apis/maps/) web-based viewer. 

The tiler source code is located in the tiling_scripts directory of the trunk.

Quick start
===========

This script has been tested on Ubuntu and CentOS linux. Your mileage may vary.

Requirements
------------

  * [Python 2.5](http://www.python.org/download/) or above
  * [libvips](http://www.vips.ecs.soton.ac.uk/vips-7.12/)
  * [libtiff](http://www.libtiff.org/) or [BigTIFF](http://www.aperio.com/bigtiff)
  * [libjpeg](http://www.ijg.org/)
  * [ImageMagick](http://www.imagemagick.org/)
  * [OpenSlide](http://openslide.org/) and pyOpenSlide (Python bindings - only needed for SVS files compressed with the "33003" or "33005" codec)

Quick Start for Ubuntu
----------------------

  * Install Ubuntu 64 bit (32 bit has not worked for us)
  * install updates (and ssh, etc.)
  * Install libvips-dev
  * install libtiff-tools
  * Download [latest VIPS](http://www.vips.ecs.soton.ac.uk/supported/)
  * configure, make, install
  * Ready to tile!



Usage
-----

For Aperio SVS files:

    python process_aperio.py [--dir dir] [--outdir outdir] 

where dir contains the Aperio SVS files to be processed and outdir is the directory where the processed images fill will be placed.


For Bacus Labs files:

    python process_bacus.py [--dir dir] [--outdir outdir] 

where dir contains the Bacus Lab directories to be processed and outdir is the directory where the processed images fill will be placed.

Details
-------

Because the source image files can be quite large, this script uses the [libvips image processing library](http://www.vips.ecs.soton.ac.uk/index.php?title=Libvips) which handles processing large images without constraints on physical memory. 

The source SVS images are TIFF files with multiple pages compressed using the JPEG or JPEG2000 codec. If the images are compressed using JPEG2000, the [BigTIFF](http://bigtiff.org/) version of libtiff will be required. If the images are compressed using the "33003" or "33005" codec, [OpenSlide](http://openslide.org/) python bindings are used to create an uncompressed TIFF. See the documentation on the [OpenSlide](http://openslide.org/formats/aperio/) site for more information.

The naming convention of the resultant 256 x 256 pixel tiles jpeg files is "tile_z_x_y.jpg" where z is the zoom level and x and y are the x and y coordinates of the tile. Because the Google Maps API assumes square source images, the x and y coordinates are offset to make the tile set appear square at a particular zoom level. Missing "virtual" tiles will be displayed as black tiles but no such tile file will exist. This saves on disk space and processing time.
