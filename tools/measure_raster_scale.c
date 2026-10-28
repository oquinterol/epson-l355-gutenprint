/* SPDX-License-Identifier: GPL-2.0-or-later
 * Measure the fixture scale in 8-bit chunky W or K rasters.
 * Report the longest thresholded horizontal run in the scale-line region,
 * including rasterized stroke endpoints.
 */
#include <cups/raster.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
 if(argc!=2 && argc!=3) return 2;
 int expect_nominal=argc==3 && strcmp(argv[2],"--expect-100mm")==0;
 if(argc==3 && !expect_nominal)return 2;
 int fd=open(argv[1],O_RDONLY); if(fd<0)return 2;
 cups_raster_t *r=cupsRasterOpen(fd,CUPS_RASTER_READ); cups_page_header2_t h;
 if(!r||!cupsRasterReadHeader2(r,&h))return 3;
 if(h.cupsBitsPerPixel!=8||h.cupsColorOrder!=CUPS_ORDER_CHUNKED||
    (h.cupsColorSpace!=CUPS_CSPACE_W&&h.cupsColorSpace!=CUPS_CSPACE_K)||
    !h.HWResolution[0]||!h.HWResolution[1]||!h.cupsHeight||h.cupsHeight>100000||
    !h.cupsWidth||h.cupsWidth>100000||h.cupsBytesPerLine<h.cupsWidth||
    h.cupsBytesPerLine>8*1024*1024)return 4;
 unsigned char *row=malloc(h.cupsBytesPerLine); if(!row)return 5;
 unsigned best=0,bestx=0,besty=0;
 for(unsigned y=0;y<h.cupsHeight;y++) {
  if(cupsRasterReadPixels(r,row,h.cupsBytesPerLine)!=h.cupsBytesPerLine)return 6;
  /* Fixture's 100 mm scale lives near the bottom (y=160 pt). */
  if(y<h.cupsHeight*73/100||y>h.cupsHeight*85/100)continue;
  unsigned len=0;
  for(unsigned x=h.cupsWidth/30;x<h.cupsWidth*3/4;x++) {
   int black=h.cupsColorSpace==CUPS_CSPACE_K ? row[x]>127 : row[x]<128;
   if(black)len++;else len=0;
   if(len>best){best=len;bestx=x+1-len;besty=y;}
  }
 }
 printf("%s: longest continuous scale-region segment %u pixels = %.3f mm at x=%u y=%u, raster dpi %ux%u\n",argv[1],best,best*25.4/h.HWResolution[0],bestx,besty,h.HWResolution[0],h.HWResolution[1]);
 double measured=best*25.4/h.HWResolution[0];
 free(row);cupsRasterClose(r);close(fd);
 /* Raster tolerance covers stroke extents and pixel quantization. */
 if(expect_nominal && (measured < 99.5 || measured > 100.5)) {
  fputs("FAIL: raster scale exceeds the 100 +/- 0.5 mm tolerance\n",stderr);
  return 7;
 }
 return 0;
}
