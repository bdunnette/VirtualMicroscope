sudo apt-get install libvips-dev libtiff5-dev libtiff-tools libjpeg-dev openslide-tools imagemagick
wget http://www.vips.ecs.soton.ac.uk/supported/current/vips-7.32.3.tar.gz
tar -zxf vips-7.32.3.tar.gz
cd vips-7.32.3
./configure
make
sudo make install
