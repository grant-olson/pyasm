rmdir /Q /S pyasm
cvs -d:pserver:grant@192.168.187.33:/usr/local/cvsroot export -r HEAD pyasm
setup.py sdist  --formats=gztar,zip
setup.py bdist_wininst
::rmdir /Q /S pyasm
