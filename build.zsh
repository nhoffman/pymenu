#!/bin/zsh

# clean up the dist directory
sudo rm -r dist build

# create the package
python setup.py sdist
cp dist/*.gz dist/Menu_current.gz 

# post on website
sendtohost=homer.u.washington.edu
echo password for ngh2@$sendtohost
scp dist/Menu_current.gz ngh2@$sendtohost:~/public_html/pikipage/piki_data/files

mkdir -p ~/dist
cp dist/Menu_current.gz ~/dist

# install the package to this system
sudo python setup.py install
sudo rm -r build
