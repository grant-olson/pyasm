rmdir /Q /S pyasm
cvs -d:pserver:grant@192.168.187.33:/usr/local/cvsroot export -r HEAD pyasm
setup.py sdist
setup.py bdist
::rmdir /Q /S pyasm
