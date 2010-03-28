del MANIFEST
rmdir /Q /S pyasm
svn export svn+ssh://grant@johnwhorfin/var/local/svn/pyasm/trunk pyasm
setup.py sdist --formats=gztar,zip
setup.py bdist_wininst
::rmdir /Q /S pyasm
