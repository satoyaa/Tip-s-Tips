#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <stdint.h>

#include "extern.h"

// タグから色を計算 (16進RGB)
// タグごとの色
// "1": 赤, "2": 青, "3": 緑, "4": 黄, "5": 白
// 複数タグの場合はRGBを平均化
static unsigned int computeTagColor(const DataItem *item) {
    unsigned int r = 0, g = 0, b = 0;
    int count = 0;

    for (int i = 0; i < 3; i++) {
        if (strcmp(item->tags[i], "Tag0") == 0) {
            continue;
        }
        if (strcmp(item->tags[i], "Tag1") == 0) {
            r += 0xFF;
        } else if (strcmp(item->tags[i], "Tag2") == 0) {
            b += 0xFF;
        } else if (strcmp(item->tags[i], "Tag3") == 0) {
            g += 0xFF;
        } else if (strcmp(item->tags[i], "Tag4") == 0) {
            r += 0xFF;
            g += 0xFF;
        } else if (strcmp(item->tags[i], "Tag5") == 0) {
            r += 0xFF;
            g += 0xFF;
            b += 0xFF;
        }
        count++;
    }

    if (count == 0) {
        return 0x000000; // タグなしは黒
    }

    r /= count;
    g /= count;
    b /= count;

    return (r << 16) | (g << 8) | b;
}

// 最良個体の保存
void save(const char *filename) {
    FILE *fp = fopen(filename, "w");
    if (fp == NULL) {
        perror("ファイルオープン失敗");
        return;
    }

    int rectNo = 1;
    for (int i = 0; i < MAX_TIPS; i++) {
        //未定義は保存しない
        if (genes[best_index][i].x == -1 && genes[best_index][i].y == -1) {
            break;
        }

        // tipの中心座標を計算
        double x_center = genes[best_index][i].x + tipWidth / 2.0;
        double y_center = genes[best_index][i].y + tipHeight / 2.0;
        
        // tipのサイズ(中心からの距離)
        double x_delta = tipWidth / 2.0;
        double y_delta = tipHeight / 2.0;

        // 回転角度 (dataset[i].rotate) に基づく中心回転
        double angle = dataset[i].rotate * M_PI / 180.0;
        double c = cos(angle);
        double s = sin(angle);

        // 4つの頂点 (左上、右上、右下、左下)
        // まず中心からの相対座標を求める
        double relX1 = -x_delta;
        double relY1 = -y_delta;
        double relX2 = x_delta;
        double relY2 = -y_delta;
        double relX3 = x_delta;
        double relY3 = y_delta;
        double relX4 = -x_delta;
        double relY4 = y_delta;

        // 回転: X = cosθ*x - sinθ*y, Y = sinθ*x + cosθ*y
        double rotX1 = relX1 * c - relY1 * s;
        double rotY1 = relX1 * s + relY1 * c;
        double rotX2 = relX2 * c - relY2 * s;
        double rotY2 = relX2 * s + relY2 * c;
        double rotX3 = relX3 * c - relY3 * s;
        double rotY3 = relX3 * s + relY3 * c;
        double rotX4 = relX4 * c - relY4 * s;
        double rotY4 = relX4 * s + relY4 * c;

        // 原点(中心)に戻す
        double x1 = x_center + rotX1;
        double y1 = y_center + rotY1;
        double x2 = x_center + rotX2;
        double y2 = y_center + rotY2;
        double x3 = x_center + rotX3;
        double y3 = y_center + rotY3;
        double x4 = x_center + rotX4;
        double y4 = y_center + rotY4;

        // 色コードを計算（タグ情報から）
        unsigned int color = computeTagColor(&dataset[i]);

        // 書き出し
        if (rectNo > 1) {
            fprintf(fp, "# Rectangle %d\n", rectNo);
        }
        fprintf(fp, "%7.3f  %7.3f  0x%06X\n", x1, y1, color);
        fprintf(fp, "%7.3f  %7.3f  0x%06X\n", x2, y2, color);
        fprintf(fp, "%7.3f  %7.3f  0x%06X\n", x3, y3, color);
        fprintf(fp, "%7.3f  %7.3f  0x%06X\n", x4, y4, color);
        fprintf(fp, "%7.3f  %7.3f  0x%06X\n", x1, y1, color);
        fprintf(fp, "\n\n");

        rectNo++;
    }

    fclose(fp);
}