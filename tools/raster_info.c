/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <cups/raster.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) return 2;
    cups_raster_t *r = cupsRasterOpen(fd, CUPS_RASTER_READ);
    if (!r) { close(fd); return 2; }
    cups_page_header2_t h;
    unsigned pages = 0;
    printf("{\"pages\":[");
    while (cupsRasterReadHeader2(r, &h)) {
        if (++pages > 4 || h.cupsColorOrder != CUPS_ORDER_CHUNKED ||
            h.cupsBytesPerLine == 0 || h.cupsBytesPerLine > 8*1024*1024 ||
            h.cupsHeight > 100000) return 3;
        unsigned char *row = malloc(h.cupsBytesPerLine);
        if (!row) return 3;
        for (unsigned y = 0; y < h.cupsHeight; ++y) {
            if (cupsRasterReadPixels(r, row, h.cupsBytesPerLine) != h.cupsBytesPerLine) {
                free(row); return 4;
            }
        }
        free(row);
        printf("%s{\"width\":%u,\"height\":%u,\"dpi\":[%u,%u],\"page_points\":[%u,%u],\"colorspace\":%u}",
            pages > 1 ? "," : "", h.cupsWidth, h.cupsHeight,
            h.HWResolution[0], h.HWResolution[1], h.PageSize[0], h.PageSize[1], h.cupsColorSpace);
    }
    printf("],\"count\":%u}\n", pages);
    cupsRasterClose(r); close(fd);
    return pages ? 0 : 5;
}
