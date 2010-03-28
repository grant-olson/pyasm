del MANIFEST
rmdir /Q /S pyasm
svn export svn+ssh://grant@johnwhorfin/var/local/svn/pyasm/trunk pyasm
setup.py sdist --formats=gztar,zip
setup.py bdist_wininst
rmdir /Q /S pyasm

cd dist
gpg --detach-sign pyasm-0.3.tar.gz
gpg --detach-sign pyasm-0.3.win32-py2.6.exe
gpg --detach-sign pyasm-0.3.zip
