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
    
    PyObject *m, *n, *o;
    /*PyObject *offset;*/

    m = Py_InitModule("structs", StructsMethods);
    n = Py_InitModule("PyObject", StructsMethods);
    o = Py_InitModule("PyVarObject", StructsMethods);
    
    StructsError = PyErr_NewException("structs.StructsError", NULL, NULL);
    Py_INCREF(StructsError);
    PyModule_AddObject(m, "StructsError", StructsError);

    load_PyObject(n);
    PyModule_AddObject(m, "PyObject", n);

    load_PyVarObject(o);
    PyModule_AddObject(m, "PyVarObject", o);
    
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
typeofRe = re.compile(r"(?P<type>\w+)\s*(?P<rest>[^;]+);")
variablesRe = re.compile(r"(\(|\)|\*\*|\*|\[|\]|\w+)[,\s]*")
names = []

def parse_filetext(filetext):
    global names
    for struct in structsRe.findall(filetext):
        body,name = struct
        if name in ('PyObject','PyVarObject', 'PyFrameObject'):
            continue
        print >> sys.stderr, "NAME", name

        startComment = body.find("/*")
        while startComment >= 0: #strip multiline comments
          endComment = body.find("*/",startComment) + 2
          body = body[:startComment] + body[endComment:]
          startComment = body.find("/*")

        lines = body.split("\n")
        isPyObject = False
        for line in lines:
            
            line = line.strip()
            if not line:
                continue
            print >> sys.stderr, "LINE:" , line
            if line.startswith("#"):
                print >> sys.stderr, "PREPROCESSOR DIRECTIVE"
                print line
            elif line == 'PyObject_HEAD':
                print >> sys.stderr, "HEADER" , line
                
                isPyObject = True
                print functionHead % {'funcname':name}
                names.append(name)
                print "    load_PyObject(sm);"
            elif line == 'PyObject_VAR_HEAD':
                print >> sys.stderr, "HEADER" , line
                
                isPyObject = True
                print functionHead % {'funcname':name}
                names.append(name)
                print "    load_PyVarObject(sm);"
            elif line:
                if isPyObject == False:
                    print >> sys.stderr, "NOT A PyObject: SKIPPING" , name
                    break
                typeof,rest = typeofRe.match(line).groups()
                print >> sys.stderr, "TYPE", typeof
                vars = variablesRe.findall(rest)
                vars.reverse()

                if typeof == "struct": # skip struct def
                    print >> sys.stderr, "STRUCT", vars
                    vars.pop()
                
                print >> sys.stderr, "!!", vars
                while vars:
                    var = vars.pop()
                    if var in ('*', '**'):
                        var = vars.pop()
                        print >> sys.stderr, "POINTER", var
                        print "    OFFSET(sm,%s,%s);" % (name, var)
                    elif var == '(':
                        print >> sys.stderr, "FUNCTION POINTER", vars
                        var = vars.pop()
                        if var != "*":
                            raise RuntimeError("Invalid FUnction Pointer format: %s" % line)
                        var = vars.pop()
                        print "    OFFSET(sm,%s,%s);" % (name, var)
                        vars = None
                    elif var == "[":

                        print >> sys.stderr, "SKIPPING ARRAY STUB" , vars
                        var = vars.pop()
                        var = vars.pop()
                        print >> sys.stderr, "!!", vars
                    else:
                        print >> sys.stderr, "normal", var
                        print "    OFFSET(sm,%s,%s);" % (name, var)

        if isPyObject == True:
            print functionTail % {'funcname':name}
                        
def parse_headers():
    for filename in [x for x in glob.glob("c:\\python24\\include\\*.h") if x not in
                     ('c:\\python24\\include\\datetime.h',
                      'c:\\python24\\include\\descrobject.h',
                      

                      'c:\\python24\\include\\genobject.h',
                      'c:\\python24\\include\\grammar.h',
                      'c:\\python24\\include\\node.h',
                      'c:\\python24\\include\\parsetok.h',
                      'c:\\python24\\include\\pyport.h',
                      'c:\\python24\\include\\pystate.h',
                      'c:\\python24\\include\\py_curses.h',

                      'c:\\python24\\include\\structmember.h',
                      'c:\\python24\\include\\structseq.h',
                      'c:\\python24\\include\\symtable.h',

                      'c:\\python24\\include\\ucnhash.h',
                      )]:
        print >> sys.stderr, "PROCESSING FILE", filename
        print "\n\n/* Generated from file %s */\n\n" % filename
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