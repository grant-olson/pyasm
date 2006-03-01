import sys

import re, sys, glob

head = """/* Copyright 2004-2005 Grant T. Olson. See license.txt for terms.*/
#include <Python.h>

/* Preprocessor abuse at it's finest.

   We could probably do all of this in a straight python file, but then
   it wouldn't be in sync with a particular build.  This insures we have
   the right offsets for our structs in a way we can't in pure python
*/

#define OFFSET_STRING(f) #f
#define OFFSET(m,s,f) \
    offset = PyInt_FromLong((long)&(((s*)0)->f)); \
    Py_INCREF(offset); \
    PyModule_AddObject(m, OFFSET_STRING(f), offset);

static PyObject *StructsError;
static PyObject *offset;

static PyMethodDef StructsMethods[] = {

    {NULL, NULL, 0, NULL}        /* Sentinel */
};

"""

body = """
static void
load_PyObject(PyObject* module)
{
    OFFSET(module,PyObject,ob_refcnt);
    OFFSET(module,PyObject,ob_type);
}

static void
load_PyVarObject(PyObject* module)
{
    load_PyObject(module);
    OFFSET(module,PyVarObject,ob_size);
}


"""

tail = """

PyMODINIT_FUNC
initstructs(void)
{
    
    PyObject *m, *n;
    /*PyObject *offset;*/

    m = Py_InitModule("structs", StructsMethods);
    n = Py_InitModule("PyObject", StructsMethods);

    StructsError = PyErr_NewException("structs.StructsError", NULL, NULL);
    Py_INCREF(StructsError);
    PyModule_AddObject(m, "StructsError", StructsError);

    load_PyObject(n);
    PyModule_AddObject(m, "PyObject", n);
    %s
}"""


functionHead = """static void
load_%(funcname)s(PyObject *structs)
{
    PyObject *sm = Py_InitModule("%(funcname)s",StructsMethods);

"""

functionTail = """

    PyModule_AddObject(structs,"%(funcname)s",sm);
}"""

structsRe = re.compile("typedef\s+struct\s*\w*\s*{(.*?)}\s*(\w+)",re.DOTALL)
typeofRe = re.compile(r"(?P<type>\w+)\s+(?P<rest>[^;]+);")
variablesRe = re.compile(r"(\*|\w+)[,\s]*")
names = []

def parse_filetext(filetext):
    global names
    for struct in structsRe.findall(filetext):
        body,name = struct
        if name in ('PyObject','PyVarObject'):
            continue
        print >> sys.stderr, "NAME", name

        print functionHead % {'funcname':name}
        names.append(name)
        startComment = body.find("/*")
        while startComment >= 0: #strip multiline comments
          endComment = body.find("*/",startComment) + 2
          body = body[:startComment] + body[endComment:]
          startComment = body.find("/*")

        lines = body.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                print >> sys.stderr, "PREPROCESSOR DIRECTIVE"
                print >> sys.stderr, line
            elif line == 'PyObject_HEAD':
                print >> sys.stderr, "HEADER" , line
                print "    load_PyObject(sm);"
            elif line == 'PyObject_VAR_HEAD':
                print >> sys.stderr, "HEADER" , line
                print "    load_PyVarObject(sm);"
            elif line:
                typeof,rest = typeofRe.match(line).groups()
                print >> sys.stderr, "TYPE", typeof
                vars = variablesRe.findall(rest)
                vars.reverse()
                while vars:
                    var = vars.pop()
                    if var == '*':
                        var = vars.pop()
                        print >> sys.stderr, "POINTER", var
                    else:
                        print >> sys.stderr, "normal", var
                    print "    OFFSET(sm,%s,%s);" % (name, var)

        print functionTail % {'funcname':name}
                        
def parse_headers():
    for filename in [x for x in glob.glob("c:\\python24\\include\\*.h") if x not in
                     ('c:\\python24\\include\\datetime.h',
                      'c:\\python24\\include\\descrobject.h',
                      'c:\\python24\\include\\fileobject.h',
                      'c:\\python24\\include\\frameobject.h',
                      'c:\\python24\\include\\genobject.h',
                      'c:\\python24\\include\\grammar.h',
                      'c:\\python24\\include\\listobject.h',
                      'c:\\python24\\include\\methodobject.h',
                      'c:\\python24\\include\\node.h',
                      'c:\\python24\\include\\object.h',
                      'c:\\python24\\include\\parsetok.h',
                      'c:\\python24\\include\\pyport.h',
                      'c:\\python24\\include\\pystate.h',
                      'c:\\python24\\include\\py_curses.h',
                      'c:\\python24\\include\\stringobject.h',
                      'c:\\python24\\include\\structmember.h',
                      'c:\\python24\\include\\structseq.h',
                      'c:\\python24\\include\\symtable.h',
                      'c:\\python24\\include\\traceback.h',
                      'c:\\python24\\include\\tupleobject.h',
                      'c:\\python24\\include\\ucnhash.h',
                      )]:
        print >> sys.stderr, "PROCESSING FILE", filename
        print "\n\n/* Generated from file %s\n\n" % filename
        f = file(filename) 
        filetext = f.read()
        f.close()
        parse_filetext(filetext)

def make_struct_c():
    print head
    print body
    parse_headers()
    print tail % ''.join(["    load_%s(m);\n" % x for x in names])

make_struct_c()