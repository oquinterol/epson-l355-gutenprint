/* SPDX-License-Identifier: GPL-2.0-or-later
 * Check a small raster ROI around each fixture mark's expected center.
 * stdin: name x_points y_points, in PostScript bottom-left coordinates.
 * Counts describe local raster-pixel presence. ROI boundaries use the header's
 * imaging box and nominal DPI.
 */
#include <cups/raster.h>
#include <fcntl.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

struct mark { char name[32]; double x,y; int x0,x1,y0,y1; unsigned dark; };

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    struct mark marks[32]; unsigned n=0;
    while(n<32) {
        int fields=scanf("%31s %lf %lf",marks[n].name,&marks[n].x,&marks[n].y);
        if(fields==EOF)break;
        if(fields!=3||!isfinite(marks[n].x)||!isfinite(marks[n].y)||
           marks[n].x<0||marks[n].x>612||marks[n].y<0||marks[n].y>792||
           strspn(marks[n].name,"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")!=strlen(marks[n].name))return 3;
        marks[n++].dark=0;
    }
    if(!n||n==32)return 3;
    int fd=open(argv[1],O_RDONLY);if(fd<0)return 4;
    cups_raster_t *r=cupsRasterOpen(fd,CUPS_RASTER_READ);cups_page_header2_t h;
    if(!r||!cupsRasterReadHeader2(r,&h))return 4;
    if(h.cupsBitsPerPixel!=8||h.cupsColorOrder!=CUPS_ORDER_CHUNKED||
       (h.cupsColorSpace!=CUPS_CSPACE_K&&h.cupsColorSpace!=CUPS_CSPACE_W)||
       !h.cupsWidth||!h.cupsHeight||h.cupsWidth>100000||h.cupsHeight>100000||
       h.cupsBytesPerLine<h.cupsWidth||h.cupsBytesPerLine>8*1024*1024||
       !h.HWResolution[0]||!h.HWResolution[1]||
       h.HWResolution[0]>20000||h.HWResolution[1]>20000||
       !isfinite(h.cupsImagingBBox[0])||!isfinite(h.cupsImagingBBox[3])||
       h.cupsImagingBBox[0]<0||h.cupsImagingBBox[0]>612||
       h.cupsImagingBBox[3]<0||h.cupsImagingBBox[3]>792)return 4;
    double dx=h.HWResolution[0]/72.0,dy=h.HWResolution[1]/72.0;
    for(unsigned i=0;i<n;i++) {
        marks[i].x0=(int)floor((marks[i].x-1.0-h.cupsImagingBBox[0])*dx);
        marks[i].x1=(int)ceil((marks[i].x+1.0-h.cupsImagingBBox[0])*dx);
        marks[i].y0=(int)floor((h.cupsImagingBBox[3]-marks[i].y-1.0)*dy);
        marks[i].y1=(int)ceil((h.cupsImagingBBox[3]-marks[i].y+1.0)*dy);
        if(marks[i].x0<0)marks[i].x0=0;
        if(marks[i].y0<0)marks[i].y0=0;
        if(marks[i].x1>(int)h.cupsWidth)marks[i].x1=(int)h.cupsWidth;
        if(marks[i].y1>(int)h.cupsHeight)marks[i].y1=(int)h.cupsHeight;
    }
    unsigned char *row=malloc(h.cupsBytesPerLine);if(!row)return 5;
    for(unsigned y=0;y<h.cupsHeight;y++) {
        if(cupsRasterReadPixels(r,row,h.cupsBytesPerLine)!=h.cupsBytesPerLine)return 6;
        for(unsigned i=0;i<n;i++) {
            if((int)y<marks[i].y0||(int)y>=marks[i].y1)continue;
            for(int x=marks[i].x0;x<marks[i].x1;x++)
                if(h.cupsColorSpace==CUPS_CSPACE_K?row[x]>127:row[x]<128)marks[i].dark++;
        }
    }
    unsigned missing=0;printf("{\"roi_radius_points\":1,\"marks\":[");
    for(unsigned i=0;i<n;i++) {
        printf("%s{\"name\":\"%s\",\"point\":[%.6f,%.6f],\"roi_pixels\":[%d,%d,%d,%d],\"dark_pixels\":%u}",
            i?",":"",marks[i].name,marks[i].x,marks[i].y,marks[i].x0,marks[i].y0,marks[i].x1,marks[i].y1,marks[i].dark);
        if(!marks[i].dark)missing++;
    }
    printf("],\"missing_near_center\":%u,\"physical_validation\":false}\n",missing);
    free(row);cupsRasterClose(r);close(fd);return missing?7:0;
}
