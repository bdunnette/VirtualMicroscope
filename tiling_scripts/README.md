Introduction
============

The SVS_tiler.py script is a python script which will convert digitized microscope slides from the [http://www.aperio.com/ Aperio ScanScope Virtual Slide] (.SVS) format into 256x256 pixel jpeg tiles suitable for use within a [http://code.google.com/apis/maps/ Google Maps API] web-based viewer. 

The tiler source code is located in the tiling_scripts directory of the trunk.

Quick start
===========

This script has been tested on Ubuntu and CentOS linux. Your mileage may vary.

Requirements
------------

  * [http://www.python.org/download/ Python 2.5] or above
  * [http://www.vips.ecs.soton.ac.uk/vips-7.12/ libvips]
  * [http://www.libtiff.org/ libtiff] or [http://www.aperio.com/bigtiff BigTIFF]
  * [http://www.ijg.org/ libjpeg]
  * [http://www.imagemagick.org/ ImageMagick]
  * [http://openslide.org/ OpenSlide] and [http://www.osc.edu/~kerwin/pyOpenSlide/ pyOpenSlide] python bindings (only needed for SVS files compressed with the "33003" or "33005" codec)

Quick Start for Ubuntu
----------------------

﻿  * ﻿  Install Ubuntu 64 bit (32 bit has not worked for us)
﻿  * ﻿  install updates (and ssh, etc.)
﻿  * ﻿  Install libvips-dev
﻿  * ﻿  install libtiff-tools
﻿  * ﻿  Download [http://www.vips.ecs.soton.ac.uk/supported/ latest VIPS] (7.20.7 at the time of this writing)
﻿  * ﻿  -configure, make, install
﻿  * ﻿  Ready to tile!



Usage
-----

For Aperio SVS files:
  > python process_aperio.py [--dir dir] [--outdir outdir] 
where dir contains the Aperio SVS files to be processed and outdir is the directory where the processed images fill will be placed.


For Bacus Labs files:
  > python process_bacus.py [--dir dir] [--outdir outdir] 
 where dir contains the Bacus Lab directories to be processed and outdir is the directory where the processed images fill will be placed.

Details
-------

Because the source image files can be quite large, this script uses the [http://www.vips.ecs.soton.ac.uk/index.php?title=Libvips libvips image processing library] which handles processing large images without constraints on physical memory. 

The source SVS images are TIFF files with multiple pages compressed using the JPEG or  JPEG2000 codec. If the images are compressed using JPEG2000, the [http://www.aperio.com/bigtiff/ BigTIFF] version of libtiff will be required. If the images are compressed using the "33003" or "33005" codec, [http://openslide.org/ OpenSlide] [http://www.osc.edu/~kerwin/pyOpenSlide/ python bindings] are used to create an uncompressed TIFF. See the documentation on the [http://openslide.org/Aperio%20format/ OpenSlide] site for more information.

The naming convention of the resultant 256 x 256 pixel tiles jpeg files is "tile_z_x_y.jpg" where z is the zoom level and x and y are the x and y coordinates of the tile. Because the Google Maps API assumes square source images, the x and y coordinates are offset to make the tile set appear square at a particular zoom level. Missing "virtual" tiles will be displayed as black tiles but no such tile file will exist. This saves on disk space and processing time.
