# DaFup

DaFup is a watch face and background upload tool for Mo Young / Da Fit binary files.

With that tool you can upload background and watch face files in binary format to your MoYoung v2 watch.

You can create your own watch faces with that [tool](https://github.com/david47k/extrathundertool) made by David Atkinson.

**NOTE: This tool is in alpha stage, so expect some bugs.**

![DaFup](https://raw.githubusercontent.com/VicGuy/DaFup/master/Preview.png)

## Supported OS

The tools were developed for Linux, however it may work on other OS if the dependencies are fulfilled. At least the CLI version may work (feedback needed).

## Dependencies

- Python 3.x
- [PyGObject](https://github.com/GNOME/pygobject) (Only for GUI version)
- [bleak](https://github.com/hbldh/bleak)

Install them using your preferred method.

In Arch Linux for example you can install through repositories:

    # pacman -S python-gobject python-bleak

## Usage

#### How to run (Linux)

First the dependencies must be fulfilled, check them above.

In a command line, give the file execution permissions:

    $ chmod +x DaFup.py

Then since it has a shebang inside, you can run it through command line or clicking directly on the file.

    $ ./DaFup.py

## Supported watches

Da Fit watches using MoYoung v2 firmware should be supported.