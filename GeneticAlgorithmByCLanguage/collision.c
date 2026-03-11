#include <math.h>
#include <stdlib.h>

#include "extern.h"
#include "collision.h"

int rectsOverlap(double x1, double y1, double rotate1,
                 double x2, double y2, double rotate2) {
    double cx1 = x1 + tipWidth / 2.0;
    double cy1 = y1 + tipHeight / 2.0;
    double cx2 = x2 + tipWidth / 2.0;
    double cy2 = y2 + tipHeight / 2.0;

    double theta1 = rotate1 * M_PI / 180.0;
    double theta2 = rotate2 * M_PI / 180.0;

    // 回転後の各辺の方向ベクトル（単位ベクトル）
    double ux1 = cos(theta1);
    double uy1 = sin(theta1);
    double vx1 = -uy1;
    double vy1 = ux1;

    double ux2 = cos(theta2);
    double uy2 = sin(theta2);
    double vx2 = -uy2;
    double vy2 = ux2;

    double hw = tipWidth / 2.0;
    double hh = tipHeight / 2.0;

    double axes[4][2] = {
        {ux1, uy1},
        {vx1, vy1},
        {ux2, uy2},
        {vx2, vy2},
    };

    for (int ai = 0; ai < 4; ai++) {
        double ax = axes[ai][0];
        double ay = axes[ai][1];

        double c1 = cx1 * ax + cy1 * ay;
        double r1 = hw * fabs(ax * ux1 + ay * uy1) + hh * fabs(ax * vx1 + ay * vy1);

        double c2 = cx2 * ax + cy2 * ay;
        double r2 = hw * fabs(ax * ux2 + ay * uy2) + hh * fabs(ax * vx2 + ay * vy2);

        if (fabs(c1 - c2) > r1 + r2) {
            return 0;
        }
    }

    return 1;
}
