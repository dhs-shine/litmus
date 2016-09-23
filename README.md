Litmus is an automated testing tool for tizen arm devices.

Buliding & installing
---------------------

1. Create an orig.tar.gz

   $ git clone http://github.com/dhs-shine/litmus
   
   $ tar cvfz litmus_0.3.1.orig.tar.gz litmus

1. Build a deb package with debuild

   $ cd litmus
   
   $ debuild

2. Install the deb package using dpkg

   $ cd ..
   
   $ sudo dpkg -i litmus_0.3.1-1_amd64.deb


Getting started
---------------

1. Create a litmus project:

   $ litmus mk myproject

2. Modify <project_path>/userscript.py and <project_path>/conf.yaml

3. Run the litmus project

   $ litmus run myproject
