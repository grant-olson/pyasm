#include <python.h>


static PyObject *WinloadError;
PyMethodDef WinloadMethods[];


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

PyMODINIT_FUNC
initwinload(void)
{
    PyObject *m;

    m = Py_InitModule("winload", WinloadMethods);

    WinloadError = PyErr_NewException("winload.winloadException", NULL, NULL);
    Py_INCREF(WinloadError);
    PyModule_AddObject(m, "error", WinloadError);
}

static PyMethodDef WinloadMethods[] = {

    {"system",  spam_system, METH_VARARGS,
     "Execute a shell command."},

    {NULL, NULL, 0, NULL}        /* Sentinel */
};
