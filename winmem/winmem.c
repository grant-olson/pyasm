#include <python.h>
#include <windows.h>

static PyObject *WinmemError;
PyMethodDef WinmemMethods[];

LPBYTE startExcMemory;
LPBYTE posExcMemory;


static PyObject *
winmem_LoadExecutableMemoryString(PyObject *self, PyObject *args)
{
	int len,dest,ok;
	const char *memString;

	ok = PyArg_ParseTuple(args, "is", &dest, &memString);
	len = strlen(memString);

	memcpy((void*)dest,memString,len);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
winmem_AllocateExecutableMemory(PyObject *self, PyObject *args)
{
	int requestedSize, pointerToMemory;

	if (!PyArg_ParseTuple(args, "i", &requestedSize))
        return NULL;

	pointerToMemory = (int)posExcMemory;
	posExcMemory = posExcMemory + requestedSize;

	return Py_BuildValue("i",pointerToMemory);
}

static PyObject *
winmem_GetCurrentExecutablePosition(PyObject *self, PyObject *args)
{
	return Py_BuildValue("i",(int)posExcMemory);
}

PyMODINIT_FUNC
initwinmem(void)
{
	PyObject *m;

	/* Allocate executable memory */
	startExcMemory = VirtualAlloc(NULL,4096,MEM_COMMIT,PAGE_EXECUTE_READWRITE);
	posExcMemory = startExcMemory;

	/* End allocation of executable memory */

    m = Py_InitModule("winmem", WinmemMethods);

    WinmemError = PyErr_NewException("winmem.WinmemException", NULL, NULL);
    Py_INCREF(WinmemError);
    PyModule_AddObject(m, "error", WinmemError);
}

static PyMethodDef WinmemMethods[] = {

	{"AllocateExecutableMemory",winmem_AllocateExecutableMemory, METH_VARARGS,
	"Allocate a chunk of memory flagged with execute privleges and return a pointer."},

	{"LoadExecutableMemoryString",winmem_LoadExecutableMemoryString, METH_VARARGS,
	"Load a string into preallocated memory with execute permissions"},

	{"GetCurrentExecutablePosition",winmem_GetCurrentExecutablePosition, METH_VARARGS,
	"Get the current memory location so we can determine patchins."},


    {NULL, NULL, 0, NULL}        /* Sentinel */
};
