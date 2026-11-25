/* =============================================================================
 * 😀 changes done here (Modified CPython file)
 * - Line 28: Injected '[GuardPVM v1.0]' flavor identifier tag into sys.version
 * - Rest of this file is standard stock CPython (😭 no changes done)
 * =============================================================================
 * FILE PURPOSE:
 * Overrides CPython's version and build-information banner strings.
 * Injects the '[GuardPVM v1.0]' flavor identifier tag into sys.version and CLI output
 * while preserving compiler bracket syntax for regex compatibility.
 * Compiled directly into the CPython binary as Python/getversion.c.
 * ============================================================================= */

/* Return the full version string. */

#include "Python.h"

#include "patchlevel.h"

static int initialized = 0;
static char version[300];

void _Py_InitVersion(void)
{
    if (initialized) {
        return;
    }
    /* 😭 no changes done (Stock CPython) */
    initialized = 1;

    /* 😀 changes done here */
    /*
     * Custom runtime branding:
     * I injected '[GuardPVM v1.0, %.80s]' inside the compiler bracket.
     * Putting it inside the compiler bracket prevents breaking external tools
     * (like platform.python_version()) that parse sys.version with regex.
     */
#ifdef Py_GIL_DISABLED
    const char *buildinfo_format = "%.80s free-threading build (%.80s) [GuardPVM v1.0, %.80s]";
#else
    const char *buildinfo_format = "%.80s (%.80s) [GuardPVM v1.0, %.80s]";
#endif

    /* 😭 no changes done (Stock CPython) */
    PyOS_snprintf(version, sizeof(version), buildinfo_format,
                  PY_VERSION, Py_GetBuildInfo(), Py_GetCompiler());
}

const char *
Py_GetVersion(void)
{
    _Py_InitVersion();
    return version;
}

// Export the Python hex version as a constant.
const unsigned long Py_Version = PY_VERSION_HEX;
