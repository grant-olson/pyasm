"""
Make both html and pdf output for reStructuredText docs
"""

from glob import glob
import os

def runCmd(cmd):
    print
    print "RUNNING CMD '%s'" % cmd
    print
    f = os.popen(cmd)
    for line in f.readlines():
        print line ,
    print
    
for file in glob("*.txt"):
    partOfName = file[:-4]
    runCmd("rst2html.py %s html\\%s.html" % (file, partOfName))
    runCmd("rst2latex.py %s pdf\\%s.tex" % (file, partOfName))
    runCmd("latex -output-directory pdf pdf/%s.tex" % partOfName)
    runCmd("dvipdfm -o pdf/%s.pdf pdf/%s.dvi" % (partOfName,partOfName))
    runCmd("del /S pdf\\*.tex")
    runCmd("del /S pdf\\*.dvi")
    runCmd("del /S pdf\\*.log")
    runCmd("del /S pdf\\*.aux")
    