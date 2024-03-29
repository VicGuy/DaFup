# DaFup

DaFup is a watch face and background upload tool for Mo Young / Da Fit binary files.

With that tool you can upload background and watch faces files in binary format to your MoYoung v2 watch.

**NOTE: This tool is in alpha stage, so expect some bugs.**


## Usage

#### Supported OS

So far it supports Linux only.

#### Dependencies

- Python 3.x
- [PyGObject](https://github.com/GNOME/pygobject)
- [bleak](https://github.com/hbldh/bleak)

Install them using your preferred method.

In Arch Linux for example you can install through repositories:

    # pacman -S python-gobject python-bleak

#### How to run

First the dependencies must be fulfilled, check them above.

In a command line, give the file execution permissions:

    $ chmod +x DaFup.py

Then run it through command line or clicking directly on the file.

    $ ./DaFup.py

## Supported watches

Da Fit watches using MoYoung v2 firmware should be supported.