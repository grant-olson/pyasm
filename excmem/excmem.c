/* Copyright 2004-2005 Grant T. Olson. See license.txt for terms.*/

/*
This provides a basic interface to allocate executable memory.  This will become
more important as W^X type protection gets used more and more.  To be honest, I'm
not sure if this is even matters at this point.  It seems like (in windows at least)
the execute permission has no effect, only removing the write permission causes a fault.

Right now this is pretty much a stub, it should eventually work more like a real 
allocator with a linked list of pages of memory that are allocated on an as-needed basis.

Also need to decide how much memory we will want to free and how that should be
implemented.

And I need to decide if it's important to make sure that we don't use WRITE and EXECUTE
permissions at the same time.
*/

#include <Python.h>

#ifdef MS_WINDOWS

#include <windows.h>

#else

#include <dlfcn.h>
#include <sys/mman.h>

#endif


static PyObject *ExcmemError;
static PyMethodDef ExcmemMethods[];

void *startExcMemory;
void *posExcMemory;


static PyObject *
excmem_LoadExecutableMemoryString(PyObject *self, PyObject *args)
{
	int len,dest,ok;
	const char *memString;

	ok = PyArg_ParseTuple(args, "is#", &dest, &memString,&len);

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

	pointerToMemory = (int)posExcMemory;
	posExcMemory = (void*)(pointerToMemory + requestedSize);

	return Py_BuildValue("i",pointerToMemory);
}

static PyObject *
excmem_GetCurrentExecutablePosition(PyObject *self, PyObject *args)
{
	return Py_BuildValue("i",(int)posExcMemory);
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

PyMODINIT_FUNC
initexcmem(void)
{
	PyObject *m;

	/* Allocate executable memory */
#ifdef MS_WINDOWS
	startExcMemory = VirtualAlloc(NULL,4096,MEM_COMMIT,PAGE_EXECUTE_READWRITE);
#else
	startExcMemory = malloc(4096);
	mprotect(startExcMemory,4096,PROT_READ|PROT_WRITE|PROT_EXEC);
#endif


	posExcMemory = startExcMemory;

	/* End allocation of executable memory */

    m = Py_InitModule("excmem", ExcmemMethods);

    ExcmemError = PyErr_NewException("excmem.ExcmemError", NULL, NULL);
    Py_INCREF(ExcmemError);
    PyModule_AddObject(m, "ExcmemError", ExcmemError);
}

#ifndef MS_WINDOWS

static PyObject *
excmem_GetSymbolAddress(PyObject *self, PyObject *args)
{
	char *libname;
	char *symname;
	void *lib_addr;
	void *sym_addr;

	if (!PyArg_ParseTuple(args, "ss", &libname, &symname))
		return NULL;

	lib_addr = dlopen(libname,RTLD_LAZY);
	sym_addr = dlsym(lib_addr,symname);

	return Py_BuildValue("i",(int)sym_addr);
}

#else

static PyObject *
excmem_GetSymbolAddress(PyObject *self, PyObject *args)
{
	Py_INCREF(Py_None);
	return Py_None;
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
