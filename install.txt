## Basic Installation

oacensus is a standard Python package and can be installed in the standard
ways. Here's one way to install, using pip, so any subsequent changes in the
source are immediately effected:

git clone https://github.com/ananelson/oacensus
cd oacensus/
sudo pip install -e .

## Troubleshooting

The only unusual thing is that the pyoai package requires the lxml package
which has strange dependencies. If you don't already have this installed, then
installing the Cython python package (pip install cython) and the libxml and
libxslt libraries in advance should help.

For example, on ubuntu:

sudo pip install cython
sudo apt-get install libxml2-dev
sudo apt-get install libxslt1-dev

Then try installing lxml using:

sudo pip install lxml

Installing this individually will help eliminate confusion over error messages.

Once lxml is installed then oacensus installation should proceed.

If this proves to be a barrier then it can be removed as a standard dependency
and only installed if pyoai is required or we can replace pyoai.

## Optional Software

Scrapers and reports might require additional software.

For example, the Personal Openness Report uses numpy, scipy and matplotlib to
generate the dotplot of open vs. total articles.
