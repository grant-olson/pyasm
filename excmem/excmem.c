/* Copyright 2004-2005 Grant T. Olson. See license.txt for terms.*/

/*
This provides a basic interface to allocate executable memory and
create PyCFunction objects.

I'm currently using PyMem_Malloc until I see a real working example
of W^X heap protection on x86 platforms.

Also need to decide how much memory we will want to free and
how that should be implemented.

And I need to decide if it's important to make sure that we
don't use WRITE and EXECUTE permissions at the same time.
*/

#include <Python.h>

#ifdef MS_WINDOWS

#include <windows.h>

#else

#include <dlfcn.h>
#include <sys/mman.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>

#endif


static PyObject *ExcmemError;


static PyObject *
excmem_LoadExecutableMemoryString(PyObject *self, PyObject *args)
{
	int len,dest;
	const char *memString;

	if (!PyArg_ParseTuple(args, "is#", &dest, &memString,&len))
		return NULL;

	memcpy((void*)dest,memString,len);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
excmem_AllocateExecutableMemory(PyObject *self, PyObject *args)
{
	int requestedSize, pointerToMemory;

	if (!PyArg_ParseTuple(args, "i", &requestedSize))
        return NULL;

	pointerToMemory = (int)PyMem_Malloc(requestedSize);

	return Py_BuildValue("i",pointerToMemory);
}

static PyObject *
excmem_GetCurrentExecutablePosition(PyObject *self, PyObject *args)
{
	PyErr_SetString(ExcmemError,"Depreciated function!");
	return 0;
}

static PyObject *
excmem_BindFunctionAddress(PyObject *self, PyObject *args)
{
	PyMethodDef *md;
	PyObject *func;
	int pointer;

	if (!PyArg_ParseTuple(args, "i", &pointer))
        return NULL;

	

	md = PyMem_New(PyMethodDef,1);
	md->ml_doc = "foo";
	md->ml_flags = METH_VARARGS;
	md->ml_meth = (void*)pointer;
	md->ml_name = "foo";

	func = PyCFunction_New(md,NULL);

	return Py_BuildValue("O",func);
}


#ifndef MS_WINDOWS

static PyObject *
excmem_GetSymbolAddress(PyObject *self, PyObject *args)
{
	char *symname;
	void *sym_addr;

	if (!PyArg_ParseTuple(args, "s", &symname))
		return NULL;

	sym_addr = dlsym(0,symname);
	if(!sym_addr) {
		PyErr_SetString(ExcmemError,"Couldn't resolve symbol");
		return NULL;
	}

	return Py_BuildValue("i",(int)sym_addr);
}

#else

static PyObject *
excmem_GetSymbolAddress(PyObject *self, PyObject *args)
{
	PyErr_SetString(ExcmemError,"Please use win32api calls to get "
                    "symbol addresses on windows.");
	return NULL;
}

#endif

static PyMethodDef ExcmemMethods[] = {

	{"AllocateExecutableMemory",excmem_AllocateExecutableMemory, METH_VARARGS,
	"Allocate a chunk of memory flagged with execute privleges and return a pointer."},

	{"LoadExecutableMemoryString",excmem_LoadExecutableMemoryString, METH_VARARGS,
	"Load a string into preallocated memory with execute permissions"},

	{"GetCurrentExecutablePosition",excmem_GetCurrentExecutablePosition, METH_VARARGS,
	"Get the current memory location so we can determine patchins."},

	{"BindFunctionAddress",excmem_BindFunctionAddress, METH_VARARGS,
	"Binds a function address to a python PyCFUnction object so we can call it."},

	{"GetSymbolAddress",excmem_GetSymbolAddress, METH_VARARGS,
	"Get an address of a symbol from a shared library or executable"},


    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initexcmem(void)
{
	
	PyObject *m;

    m = Py_InitModule("excmem", ExcmemMethods);

    ExcmemError = PyErr_NewException("excmem.ExcmemError", NULL, NULL);
    Py_INCREF(ExcmemError);
	PyModule_AddObject(m, "ExcmemError", ExcmemError);

}
