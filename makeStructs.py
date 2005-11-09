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

static void
load_PyCellObject(PyObject *structs)
{
    PyObject *sm = Py_InitModule("PyCellObject", StructsMethods);
    
    load_PyObject(sm);
    OFFSET(sm,PyCellObject,ob_ref);

    PyModule_AddObject(structs,"PyCellObject",sm);
}

static void
load_PyClassObject(PyObject *structs)
{
    PyObject *sm = Py_InitModule("PyClassObject", StructsMethods);

    load_PyObject(sm);
    OFFSET(sm,PyClassObject,cl_bases);
    OFFSET(sm,PyClassObject,cl_dict);
    OFFSET(sm,PyClassObject,cl_name);

    OFFSET(sm,PyClassObject,cl_getattr);
    OFFSET(sm,PyClassObject,cl_setattr);
    OFFSET(sm,PyClassObject,cl_delattr);

    PyModule_AddObject(structs,"PyClassObject",sm);
}

static void
load_PyInstanceObject(PyObject *structs)
{
    PyObject *sm = Py_InitModule("PyInstanceObject",StructsMethods);

    load_PyObject(sm);
    OFFSET(sm,PyInstanceObject,in_class);
    OFFSET(sm,PyInstanceObject,in_dict);    
    OFFSET(sm,PyInstanceObject,in_weakreflist);

    PyModule_AddObject(structs,"PyInstanceObject",sm);
}


static void
load_PyMethodObject(PyObject *structs)
{
    PyObject *sm = Py_InitModule("PyMethodObject",StructsMethods);

    load_PyObject(sm);
    OFFSET(sm,PyMethodObject,im_func);
    OFFSET(sm,PyMethodObject,im_self);
    OFFSET(sm,PyMethodObject,im_class);
    OFFSET(sm,PyMethodObject,im_weakreflist);

    PyModule_AddObject(structs,"PyMethodObject",sm);
}


static void
load_PyString(PyObject *structs)
{
    PyObject *sm = Py_InitModule("PyString", StructsMethods);
    
    load_PyVarObject(sm);
    OFFSET(sm,PyStringObject,ob_shash);
    OFFSET(sm,PyStringObject,ob_sstate);
    OFFSET(sm,PyStringObject,ob_sval);

    PyModule_AddObject(structs,"PyString",sm);
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
    load_PyCellObject(m);
    load_PyClassObject(m);
    load_PyInstanceObject(m);
    load_PyMethodObject(m);
    load_PyString(m);
}"""

import re

f = file("c:\\python24\\include\\object.h") #stringobject.h")
filetext = f.read()
f.close()

structs = re.findall("typedef\s+struct\s*\w*\s*{(.*?)}\s*(\w+)",filetext,re.DOTALL)

for struct in structs:
    body,name = struct
    print "NAME", name
  
    startComment = body.find("/*")
    while startComment >= 0: #strip multiline comments
      endComment = body.find("*/",startComment) + 2
      body = body[:startComment] + body[endComment:]
      startComment = body.find("/*")

    lines = body.split("\n")
    for line in lines:
        line = line.strip()
        if line:
            print "LINE: ", line