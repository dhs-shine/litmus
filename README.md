Litmus is an automated testing tool for tizen arm devices.


Prerequisite
---------------------

Litmus uses sdb to communicate with device.
sdb is not released on download.tizen.org/tools but you can find it from sdk.

Install sdb from tizen sdk or download binary from below url.

32bit:
http://download.tizen.org/sdk/tizenstudio/official/binary/sdb_2.2.89_ubuntu-32.zip

64bit:
http://download.tizen.org/sdk/tizenstudio/official/binary/sdb_2.2.89_ubuntu-64.zip

Unzip this package and copy sdb binary to /usr/bin


Buliding & installing
---------------------

1. Clone this project

   $ git clone https://github.com/dhs-shine/litmus
   
1. Build a deb package with debuild

   $ cd litmus
   
   $ debuild

2. Install the deb package by using dpkg

   $ cd ..
   
   $ sudo dpkg -i litmus_0.3.1-1_amd64.deb


Getting started
---------------

1. Create a litmus project:

   $ litmus mk [project_name]

2. Modify [project_path]/userscript.py and [project_path]/conf.yaml

3. Run the litmus project

   $ litmus run [project_name]


Please refer to litmus wiki for more details.


https://github.com/dhs-shine/litmus/wiki

https://wiki.tizen.org/wiki/Litmus
