/* The byte counter, in C.
 *
 * Kept deliberately small: the point of the stack is the extension plumbing
 * (parsing arguments without copying, refusing the wrong type, releasing the
 * GIL is NOT done here because a 10 MB string is microseconds) and the fact
 * that the tests can compare it against the pure-Python reference on random
 * input rather than on three hand-written fixtures.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

static int is_separator(unsigned char byte)
{
    switch (byte) {
    case ' ':
    case '\t':
    case '\n':
    case '\r':
    case '\v':
    case '\f':
        return 1;
    default:
        return 0;
    }
}

static PyObject *count_bytes(PyObject *self, PyObject *args)
{
    Py_buffer view;
    Py_ssize_t size;
    Py_ssize_t index;
    Py_ssize_t lines = 0;
    Py_ssize_t words = 0;
    int inside_word = 0;

    (void)self;

    /* "y*" takes any contiguous buffer -- bytes, bytearray, memoryview -- and
     * hands back a length, so embedded NUL bytes are counted like any other
     * byte ("s#" would stop at the first one, and "y#" refuses a bytearray). */
    if (!PyArg_ParseTuple(args, "y*:count_bytes", &view)) {
        return NULL;
    }

    size = view.len;
    for (index = 0; index < size; index++) {
        unsigned char byte = ((const unsigned char *)view.buf)[index];
        if (byte == '\n') {
            lines++;
        }
        if (is_separator(byte)) {
            inside_word = 0;
        } else if (!inside_word) {
            inside_word = 1;
            words++;
        }
    }

    PyBuffer_Release(&view);
    return Py_BuildValue("(nnn)", lines, words, size);
}

static PyObject *count_str(PyObject *self, PyObject *args)
{
    PyObject *text = NULL;
    PyObject *encoded = NULL;
    PyObject *result = NULL;
    PyObject *tuple = NULL;

    (void)self;

    if (!PyArg_ParseTuple(args, "U:count_str", &text)) {
        return NULL;
    }
    encoded = PyUnicode_AsEncodedString(text, "utf-8", "strict");
    if (encoded == NULL) {
        return NULL;
    }
    tuple = Py_BuildValue("(O)", encoded);
    if (tuple == NULL) {
        Py_DECREF(encoded);
        return NULL;
    }
    result = count_bytes(NULL, tuple);
    Py_DECREF(tuple);
    Py_DECREF(encoded);
    return result;
}

static PyObject *separators(PyObject *self, PyObject *unused)
{
    static const char bytes[] = {' ', '\t', '\n', '\r', '\v', '\f'};
    (void)self;
    (void)unused;
    return Py_BuildValue("y#", bytes, (Py_ssize_t)sizeof(bytes));
}

static PyMethodDef methods[] = {
    {"count_bytes", count_bytes, METH_VARARGS,
     "count_bytes(data) -> (lines, words, bytes)\n\n"
     "Count a bytes-like object. Embedded NUL bytes are ordinary bytes."},
    {"count_str", count_str, METH_VARARGS,
     "count_str(text) -> (lines, words, bytes)\n\n"
     "Encode to UTF-8 first, then count bytes."},
    {"separators", separators, METH_NOARGS,
     "separators() -> bytes\n\nThe six ASCII bytes treated as word breaks."},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "_speedups",
    "Byte-level counters for text statistics.",
    -1,
    methods,
    NULL,
    NULL,
    NULL,
    NULL,
};

PyMODINIT_FUNC PyInit__speedups(void)
{
    PyObject *handle = PyModule_Create(&module);
    if (handle == NULL) {
        return NULL;
    }
    if (PyModule_AddStringConstant(handle, "__version__", "1.0") < 0) {
        Py_DECREF(handle);
        return NULL;
    }
    return handle;
}
