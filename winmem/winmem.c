#include <python.h>
#include <windows.h>

static PyObject *WinloadError;
PyMethodDef WinloadMethods[];

LPBYTE startExcMemory;
LPBYTE posExcMemory;


static PyObject *
spam_system(PyObject *self, PyObject *args)
{
    const char *command;
    int sts;

    if (!PyArg_ParseTuple(args, "s", &command))
        return NULL;
    sts = system(command);
    return Py_BuildValue("i", sts);
}

static PyObject *
winload_LoadExecutableMemory(PyObject *self, PyObject *args)
{
	int len, ok;
	const char *memString;

	ok = PyArg_ParseTuple(args, "s", &memString);
	len = strlen(memString);

	memcpy(posExcMemory,memString,len);
	posExcMemory = posExcMemory + len;

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
winload_GetCurrentPosition(PyObject *self, PyObject *args)
{
	return Py_BuildValue("i",(int)posExcMemory);
}

PyMODINIT_FUNC
initwinload(void)
{
	PyObject *m;

	/* Allocate executable memory */
	startExcMemory = VirtualAlloc(NULL,4096,MEM_COMMIT,PAGE_EXECUTE_READWRITE);
	posExcMemory = startExcMemory;

	/* End allocation of executable memory */

    m = Py_InitModule("winload", WinloadMethods);

    WinloadError = PyErr_NewException("winload.winloadException", NULL, NULL);
    Py_INCREF(WinloadError);
    PyModule_AddObject(m, "error", WinloadError);
}

static PyMethodDef WinloadMethods[] = {

    {"system",  spam_system, METH_VARARGS,
     "Execute a shell command."},
	{"LoadExecutableMemory",winload_LoadExecutableMemory, METH_VARARGS,
	"Load a string into preallocated memory with execute permissions"},
	{"GetCurrentPosition",winload_GetCurrentPosition, METH_VARARGS,
	"Get the current memory location so we can determine patchins."},


    {NULL, NULL, 0, NULL}        /* Sentinel */
};
