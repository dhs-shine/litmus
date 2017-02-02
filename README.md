Litmus is an automated testing tool for tizen arm devices.


# Prerequisite

Litmus uses sdb to communicate with device.
sdb is not released on download.tizen.org/tools but you can find it from sdk.

Install sdb from tizen sdk or download binary from below url.

32bit:
    https://download.tizen.org/sdk/tizenstudio/official/binary/sdb_2.3.0_ubuntu-32.zip

64bit:
    https://download.tizen.org/sdk/tizenstudio/official/binary/sdb_2.3.0_ubuntu-64.zip

Unzip this package and copy sdb binary to /usr/bin

    $ wget http://download.tizen.org/sdk/tizenstudio/official/binary/sdb_2.3.0_ubuntu-64.zip \
      && unzip sdb_2.3.0_ubuntu-64.zip -d ./temp \
      && sudo cp ./temp/data/tools/sdb /usr/bin \
      && rm -f sdb_2.3.0_ubuntu-64.zip \
      && rm -rf ./temp


# Buliding & installing

Clone this project

    $ git clone https://github.com/dhs-shine/litmus
   
Build a deb package with debuild

    $ cd litmus
    $ debuild

Install the deb package by using dpkg

    $ cd ..
    $ sudo dpkg -i litmus_0.3.5-1_amd64.deb


Getting started
---------------

Create a litmus project:

    $ litmus mk [project_name]

Modify [project_path]/userscript.py and [project_path]/conf.yaml

Run the litmus project

    $ litmus run [project_name]


Please refer to litmus wiki for more details.

  https://github.com/dhs-shine/litmus/wiki
  https://wiki.tizen.org/wiki/Litmus
