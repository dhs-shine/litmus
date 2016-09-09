Litmus is an automated testing tool for tizen arm devices.

Buliding & installing
---------------------

1. Build a deb package with debuild

2. Install the deb package using dpkg

   $ sudo dpkg -i litmus_0.2.1-1_amd64.deb


Getting started
---------------

1. Create a litmus project:

   $ litmus mk myproject

2. Modify <project_path>/userscript.py and <project_path>/conf.yaml

3. Run the litmus project

   $ litmus run myproject
