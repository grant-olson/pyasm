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
    
for f in glob("*.txt"):
    try:
        partOfName = f[:-4]
        runCmd("rst2html.py %s html\\%s.html" % (f, partOfName))
        runCmd("rst2latex.py %s pdf\\%s.tex" % (f, partOfName))
        runCmd("latex -output-directory pdf pdf/%s.tex" % partOfName)

        # don't use ugly Computer Modern font
        tmpFile = file("pdf/%s.tex" % partOfName).read()
        tmpFile = tmpFile.replace("%% generator Docutils: ",
                                  "\usepackage{times}\n%% generator Docutils: ")
        f = file("pdf/%s.tex","w")
        f.write(tmpFile)
        f.close()

        runCmd("dvipdfm -o pdf/%s.pdf pdf/%s.dvi" % (partOfName,partOfName))
    except:
        print "Processing %s failed" % f
    
#runCmd("del /S pdf\\*.tex")
runCmd("del /S pdf\\*.dvi")
runCmd("del /S pdf\\*.log")
runCmd("del /S pdf\\*.aux")
    