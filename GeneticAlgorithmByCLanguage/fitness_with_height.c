#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "extern.h"

void calc_fitness_with_height() {
    for (int i = 0; i < POPULATION; i++) {
        int sumHeight = 0;
        int varianceHeight = 0;
        // 各タグごとの集計用配列（動的に num_tags 個分確保）
        int tagCount[num_tags];
        double tagSumX[num_tags];
        double tagSumY[num_tags];
        double tagCenterX[num_tags];
        double tagCenterY[num_tags];
        double tagVariance[num_tags];

        // 配列の初期化
        for (int t = 0; t < num_tags; t++) {
            tagCount[t] = 0;
            tagSumX[t] = 0.0;
            tagSumY[t] = 0.0;
            tagCenterX[t] = 0.0;
            tagCenterY[t] = 0.0;
            tagVariance[t] = 0.0;
        }

        // １．中心を計算
        for (int j = 0; j < max_tips; j++) {
            sumHeight += genes[i][j].y; // ここで高さの合計を計算
            for (int t = 0; t < num_tags; t++) {
                // dataset[j]が持ついずれかのタグと、Taglist[t]が一致するか判定
                int isTag = (strcmp(dataset[j].tags[0], Taglist[t]) == 0) ||
                            (strcmp(dataset[j].tags[1], Taglist[t]) == 0) ||
                            (strcmp(dataset[j].tags[2], Taglist[t]) == 0);

                if (isTag) {
                    tagSumX[t] += genes[i][j].x;
                    tagSumY[t] += genes[i][j].y;
                    tagCount[t]++;
                }
            }
        }

        // 中心座標の算出
        for (int t = 0; t < num_tags; t++) {
            if (tagCount[t] > 0) {
                tagCenterX[t] = tagSumX[t] / tagCount[t];
                tagCenterY[t] = tagSumY[t] / tagCount[t];
            }
        }

        // ２．分散を計算
        for (int j = 0; j < max_tips; j++) {
            varianceHeight += pow(genes[i][j].y - (sumHeight / max_tips), 2); // 高さの分散を計算
            for (int t = 0; t < num_tags; t++) {
                int isTag = (strcmp(dataset[j].tags[0], Taglist[t]) == 0) ||
                            (strcmp(dataset[j].tags[1], Taglist[t]) == 0) ||
                            (strcmp(dataset[j].tags[2], Taglist[t]) == 0);

                if (isTag) {
                    tagVariance[t] += pow(genes[i][j].x - tagCenterX[t], 2) + 
                                      pow(genes[i][j].y - tagCenterY[t], 2);
                }
            }
        }

        // ３．適応度は分散の合計
        fitness[i] = 0.0;
        for (int t = 0; t < num_tags; t++) {
            fitness[i] += tagVariance[t];
        }
        fitness[i] += sumHeight*WEIGHT; // 高さの合計も適応度に加算
        /*
        //内訳表示
        for (int t = 0; t < num_tags; t++)
        {
            printf("Individual %d, Tag %s: Count = %d, Center = (%.2f, %.2f), Variance = %.2f\n", 
                   i, Taglist[t], tagCount[t], tagCenterX[t], tagCenterY[t], tagVariance[t]);
        }*/
        
        //内訳表示
        /*
        printf("Individual %d: Fitness = %f (Height Sum = %d, Height Variance = %d)\n", 
               i, fitness[i], sumHeight, varianceHeight);*/
    }
}