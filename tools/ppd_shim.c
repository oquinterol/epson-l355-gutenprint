/* SPDX-License-Identifier: GPL-2.0-or-later
 * Supply an explicit local test PPD through the public CUPS cupsGetPPD API.
 * L355_TEST_PPD selects the fixture used by the sandboxed filter.
 */
#include <stdlib.h>
#include <stdio.h>

const char *cupsGetPPD(const char *printer)
{
    (void) printer;
    const char *path = getenv("L355_TEST_PPD");
    if (!path || path[0] != '/') {
        fputs("L355 offline shim: missing explicit PPD path\n", stderr);
        return NULL;
    }
    fputs("L355 offline shim: cupsGetPPD uses local fixture\n", stderr);
    return path;
}
