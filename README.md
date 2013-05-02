VirtualMicroscope
=================
This application was developed by an academic lab for our specific educational environment. This software will not run 'out of the box' at your school - you will need technical staff proficient in Python, Django, and general web technologies to set up and integrate it into your local environment.

1.  Set up your development machine with Python, MySQL, Python Imaging Library, and Django (now requires version 1.4 or greater). Django Guides:
[Django Quick install guide](https://docs.djangoproject.com/en/1.5/intro/install/)
[Django - Deploying to a production web server](https://docs.djangoproject.com/en/1.5/howto/deployment/)

2. Create a Django Project for your local instance.

3. In that project, install both Version 2 of the NYUVM and [Django Compressor](https://pypi.python.org/pypi/django_compressor) (now required for performance reasons).
This involves:
  * Copying the app folders into the project
  * Adding both apps to INSTALLED_APPS 
  * Adding references to the NYUVM url file to the project-level urls.py. In our instance it looks like:
    *url(r'^virtualmicroscope/',include('nyuvm.urls')),*
  * Configuring local authentication and/or user registration as you see fit
  * Configuring your database and running sync-db

4. In addition to any settings you want to configure for Compressor, There are several ones for the NYUVM you can add to your settings.py

*Required Settings:*

Enable the admin app in settings.py and urls.py

Optional VM Specific Settings:

    URL_ROOT= '/virtualmicroscope'  #the base url prefix.  You can optionally omit this and handle at the apache conf level using the ‘PythonOption django.root’ setting.
    REQ_LOGIN = False  #require login for all slide and collection views
    COMPRESS_ENABLED=True #override and force compressor even on dev server
    COMM_MARKER_EXPIRE = 180 #number of days untila a community marker expires
    SLIDES_PER_PAGE = 150 #number of thumbnails per page
    API_KEY = 'xxxxxxx' #google maps API key (optional)
    GAKEY = 'xxxxx' #google analytics key (optional)

5. At this point your development Django server should run and you can begin adding slides and collections [http://dei.med.nyu.edu/help/virtualmicroscope/administrators as per the documentation].

Simple slide viewer template
============================


Introduction
------------

This is a code snippet to create an HTML page with a slide viewer.  This snippet is just a simple viewer with navigation and points to a slide on the NYU School of Medicine's cloud servers.  You could use this as a template to build your own database-driven viewer system.


Code Snippet
------------

    <html><head> 
    
    <script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=true"></script> 
    <script type="text/javascript"> 
    var map;
     
    function initialize() 
    {
            geocoder = new google.maps.Geocoder();
    
            var myOptions = {
                    zoom: 2,
                    center: new google.maps.LatLng(0,0),
                    mapTypeControl: false,
                    navigationControl: true,
                    mapTypeId: google.maps.MapTypeId.ROADMAP
            }
    
            map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);
    
            var VM_Map = new google.maps.ImageMapType({
                                    name: 'NYU Virtual Microscope', 
                                    alt: 'NYU Virtual Microscope',
                                    getTileUrl: function(coord, zoom) {return customGetTileUrl(coord, zoom);},
                                    tileSize: new google.maps.Size(256, 256),
                                    minZoom: 1, 
                                    maxZoom: 8, 
                                    isPng: false
                            });
            
                            map.mapTypes.set('VM_Map', VM_Map);
    
            map.setMapTypeId('VM_Map');
    }
    
    
     function customGetTileUrl(coord,zoom) {
            return "http://c3384049.r49.cf0.rackcdn.com/tile_" + zoom + "_"+ coord.x + "_" + coord.y + ".jpg"
    };
    </script> 
    
    </head> 
    <body id="body" style="margin:0px; padding:0px; overflow: hidden;" onLoad="initialize()" > 
                    <div id="map_canvas" style="width:100%; height: 100%;"></div> 
    </body> 
    </html>
