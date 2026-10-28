/* SPDX-License-Identifier: GPL-2.0-or-later
 * Locate long dark contours near the raster edges of synthetic Letter frames.
 * Input format: 8-bit chunky W or K.
 */
#include <cups/raster.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static void bands(const unsigned *counts, unsigned size, unsigned threshold, unsigned limit)
{
    unsigned count = 0;
    putchar('[');
    for (unsigned i = 0; i < size; ++i) {
        if (i >= limit && i + limit < size) continue;
        if (counts[i] <= threshold) continue;
        unsigned start = i;
        while (i + 1 < size && counts[i + 1] > threshold) ++i;
        printf("%s[%u,%u]", count++ ? "," : "", start, i);
    }
    putchar(']');
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) return 2;
    cups_raster_t *r = cupsRasterOpen(fd, CUPS_RASTER_READ);
    cups_page_header2_t h;
    if (!r || !cupsRasterReadHeader2(r, &h)) return 3;
    if (h.cupsBitsPerPixel != 8 || h.cupsColorOrder != CUPS_ORDER_CHUNKED ||
        (h.cupsColorSpace != CUPS_CSPACE_K && h.cupsColorSpace != CUPS_CSPACE_W) ||
        !h.cupsWidth || !h.cupsHeight || h.cupsWidth > 100000 || h.cupsHeight > 100000 ||
        h.cupsBytesPerLine < h.cupsWidth || h.cupsBytesPerLine > 8*1024*1024 ||
        !h.HWResolution[0] || !h.HWResolution[1]) return 4;
    unsigned *rows = calloc(h.cupsHeight, sizeof(unsigned));
    unsigned *cols = calloc(h.cupsWidth, sizeof(unsigned));
    unsigned char *row = malloc(h.cupsBytesPerLine);
    if (!rows || !cols || !row) return 5;
    for (unsigned y = 0; y < h.cupsHeight; ++y) {
        if (cupsRasterReadPixels(r, row, h.cupsBytesPerLine) != h.cupsBytesPerLine) return 6;
        for (unsigned x = 0; x < h.cupsWidth; ++x) {
            int dark = h.cupsColorSpace == CUPS_CSPACE_K ? row[x] > 127 : row[x] < 128;
            if (!dark) continue;
            if (x >= h.cupsWidth/10 && x < h.cupsWidth*9/10) ++rows[y];
            if (y >= h.cupsHeight/10 && y < h.cupsHeight*9/10) ++cols[x];
        }
    }
    printf("{\"pixels\":[%u,%u],\"dpi\":[%u,%u],\"page_points\":[%.6f,%.6f],",
        h.cupsWidth,h.cupsHeight,h.HWResolution[0],h.HWResolution[1],h.cupsPageSize[0],h.cupsPageSize[1]);
    printf("\"imaging_bbox_points\":[%.6f,%.6f,%.6f,%.6f],",
        h.cupsImagingBBox[0],h.cupsImagingBBox[1],h.cupsImagingBBox[2],h.cupsImagingBBox[3]);
    printf("\"horizontal_line_row_bands\":");
    bands(rows,h.cupsHeight,h.cupsWidth/2,h.HWResolution[1]/2);
    printf(",\"vertical_line_column_bands\":");
    bands(cols,h.cupsWidth,h.cupsHeight/2,h.HWResolution[0]/2);
    printf(",\"method\":\"thresholded long-line projections near raster edges\"}\n");
    free(rows);free(cols);free(row);cupsRasterClose(r);close(fd);return 0;
}
