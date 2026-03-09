#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "extern.h"

// 回転矩形の衝突判定（SAT：分離軸定理）
//  - x,y: 左上座標
//  - rotate: 回転角度（°）
static int rectsOverlap(double x1, double y1, double rotate1,
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

void initialize(){
    //配列初期化
    for (int i = 0; i < POPULATION; i++)
    {
        for (int j = 0; j < MAX_TIPS; j++)
        {
            //使わないtipはx,yともに-1とするため，初期値は-1とする
            genes[i][j].x = -1;
            genes[i][j].y = -1;
        }   
    }
    for (int i = 0; i < POPULATION; i++)
    {
        int currentMaxHeight = tipHeight;
        for (int j = 0; j < MAX_TIPS; j++)
        {
            int x = rand()%(maxWidth-tipWidth);
            int y = rand()%(currentMaxHeight);
            //tip同士が重ならないか判定
            //tipはx,y,x+幅，y+高さの四角形とみなす
            //tipの高さと幅はすべての同じとする
            //重なる場合は再度乱数生成
            
            while (1)
            {
                int flag = 1;
                for (int k = 0; k < MAX_TIPS; k++)
                {
                    //未定義のtip
                    if (genes[i][k].x == -1 && genes[i][k].y == -1)
                    {
                        break;
                    }
                            // 回転後の座標で重なり判定
                    if (rectsOverlap(x, y, dataset[j].rotate,
                                     genes[i][k].x, genes[i][k].y, dataset[k].rotate))
                    {
                        // 重なる場合は再度乱数生成
                        x = rand()%(maxWidth-tipWidth);
                        y = rand()%(currentMaxHeight);
                        flag = 0;
                        break;
                    }

                }
                if(flag){
                    break;
                }
            }
            genes[i][j].x = x;
            genes[i][j].y = y;
            currentMaxHeight = (currentMaxHeight > y + tipHeight) ? currentMaxHeight : y + tipHeight;
        }
    }
}