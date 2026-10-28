/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <gutenprint/gutenprint.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define CHECK(expr) do { if (!(expr)) { fprintf(stderr, "FAIL: %s\n", #expr); exit(1); } } while (0)

int main(void)
{
    CHECK(stp_init() == 0);
    const stp_printer_t *p = stp_get_printer_by_driver("escp2-l355-experimental");
    CHECK(p != NULL);
    CHECK(stp_printer_get_model(p) == 355);
    stp_vars_t *v = stp_vars_create();
    stp_set_printer_defaults(v, p);
    stp_set_string_parameter(v, "PageSize", "Letter");
    stp_set_string_parameter(v, "MediaType", "Plain");
    stp_set_boolean_parameter(v, "FullBleed", 0);
    stp_dimension_t width, height, left, right, bottom, top;
    stp_get_media_size(v, &width, &height);
    stp_get_imageable_area(v, &left, &right, &bottom, &top);
    CHECK(fabs(width - 612) < 0.01 && fabs(height - 792) < 0.01);
    /* Gutenprint 5.3.5 parses model margins through unsigned long data[4].
       Round 3 mm (8.5039 pt) upward to a representable 9 pt margin. */
    const double margin = 9.0;
    CHECK(fabs(left - margin) < 0.01);
    CHECK(fabs(top - margin) < 0.01);
    CHECK(fabs((width - right) - margin) < 0.01);
    CHECK(fabs((height - bottom) - margin) < 0.01);
    stp_parameter_t desc;
    stp_describe_parameter(v, "FullBleed", &desc);
    CHECK(!desc.is_active);
    stp_parameter_description_destroy(&desc);
    stp_dimension_t maxw, maxh, minw, minh;
    stp_get_size_limit(v, &maxw, &maxh, &minw, &minh);
    CHECK(fabs(maxw - 612) < 0.01 && fabs(maxh - 1008) < 0.01);
    printf("Loaded %s; Letter margins %.4f/%.4f/%.4f/%.4f pt; borderless disabled; max media %.0fx%.0f pt\n",
           stp_printer_get_long_name(p), left, width-right, top, height-bottom, maxw, maxh);
    stp_vars_destroy(v);
    return 0;
}
