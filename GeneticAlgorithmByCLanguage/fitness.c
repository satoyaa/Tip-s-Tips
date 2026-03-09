#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "extern.h"

void calc_fitness(){
    for (int i = 0; i < POPULATION; i++)
    {
        // 適応度計算:同じタグをもつtip同士の中心からの距離の分散
        Tags tagCount = {0, 0, 0, 0, 0};
        Tags tagSumX = {0, 0, 0, 0, 0};
        Tags tagSumY = {0, 0, 0, 0, 0};
        Tags tagCenterX = {0, 0, 0, 0, 0};
        Tags tagCenterY = {0, 0, 0, 0, 0};
        //１．中心を計算
        for (int j = 0; j < MAX_TIPS; j++)
        {
            tagSumX.Tag1 += (genes[i][j].x * (dataset[j].tags[0][3] == 'Tag1' || dataset[j].tags[1][3] == 'Tag1' || dataset[j].tags[2][3] == 'Tag1'));
            tagSumY.Tag1 += (genes[i][j].y * (dataset[j].tags[0][3] == 'Tag1' || dataset[j].tags[1][3] == 'Tag1' || dataset[j].tags[2][3] == 'Tag1'));
            tagSumX.Tag2 += (genes[i][j].x * (dataset[j].tags[0][3] == 'Tag2' || dataset[j].tags[1][3] == 'Tag2' || dataset[j].tags[2][3] == 'Tag2'));
            tagSumY.Tag2 += (genes[i][j].y * (dataset[j].tags[0][3] == 'Tag2' || dataset[j].tags[1][3] == 'Tag2' || dataset[j].tags[2][3] == 'Tag2'));
            tagSumX.Tag3 += (genes[i][j].x * (dataset[j].tags[0][3] == 'Tag3' || dataset[j].tags[1][3] == 'Tag3' || dataset[j].tags[2][3] == 'Tag3'));
            tagSumY.Tag3 += (genes[i][j].y * (dataset[j].tags[0][3] == 'Tag3' || dataset[j].tags[1][3] == 'Tag3' || dataset[j].tags[2][3] == 'Tag3'));
            tagSumX.Tag4 += (genes[i][j].x * (dataset[j].tags[0][3] == 'Tag4' || dataset[j].tags[1][3] == 'Tag4' || dataset[j].tags[2][3] == 'Tag4'));
            tagSumY.Tag4 += (genes[i][j].y * (dataset[j].tags[0][3] == 'Tag4' || dataset[j].tags[1][3] == 'Tag4' || dataset[j].tags[2][3] == 'Tag4'));
            tagSumX.Tag5 += (genes[i][j].x * (dataset[j].tags[0][3] == 'Tag5' || dataset[j].tags[1][3] == 'Tag5' || dataset[j].tags[2][3] == 'Tag5'));
            tagSumY.Tag5 += (genes[i][j].y * (dataset[j].tags[0][3] == 'Tag5' || dataset[j].tags[1][3] == 'Tag5' || dataset[j].tags[2][3] == 'Tag5'));
            tagCount.Tag1 += (dataset[j].tags[0][3] == 'Tag1' || dataset[j].tags[1][3] == 'Tag1' || dataset[j].tags[2][3] == 'Tag1');
            tagCount.Tag2 += (dataset[j].tags[0][3] == 'Tag2' || dataset[j].tags[1][3] == 'Tag2' || dataset[j].tags[2][3] == 'Tag2');
            tagCount.Tag3 += (dataset[j].tags[0][3] == 'Tag3' || dataset[j].tags[1][3] == 'Tag3' || dataset[j].tags[2][3] == 'Tag3');
            tagCount.Tag4 += (dataset[j].tags[0][3] == 'Tag4' || dataset[j].tags[1][3] == 'Tag4' || dataset[j].tags[2][3] == 'Tag4');
            tagCount.Tag5 += (dataset[j].tags[0][3] == 'Tag5' || dataset[j].tags[1][3] == 'Tag5' || dataset[j].tags[2][3] == 'Tag5');
        }
        if (tagCount.Tag1 > 0) {
            tagCenterX.Tag1 = tagSumX.Tag1 / tagCount.Tag1;
            tagCenterY.Tag1 = tagSumY.Tag1 / tagCount.Tag1;
        }
        if (tagCount.Tag2 > 0) {
            tagCenterX.Tag2 = tagSumX.Tag2 / tagCount.Tag2;
            tagCenterY.Tag2 = tagSumY.Tag2 / tagCount.Tag2;
        }
        if (tagCount.Tag3 > 0) {
            tagCenterX.Tag3 = tagSumX.Tag3 / tagCount.Tag3;
            tagCenterY.Tag3 = tagSumY.Tag3 / tagCount.Tag3;
        }
        if (tagCount.Tag4 > 0) {
            tagCenterX.Tag4 = tagSumX.Tag4 / tagCount.Tag4;
            tagCenterY.Tag4 = tagSumY.Tag4 / tagCount.Tag4;
        }
        if (tagCount.Tag5 > 0) {
            tagCenterX.Tag5 = tagSumX.Tag5 / tagCount.Tag5;
            tagCenterY.Tag5 = tagSumY.Tag5 / tagCount.Tag5;
        }
        //２．分散を計算
        Tags tagVariance = {0, 0, 0, 0, 0};
        for (int j = 0; j < MAX_TIPS; j++){
            if (dataset[j].tags[0][3] == 'Tag1' || dataset[j].tags[1][3] == 'Tag1' || dataset[j].tags[2][3] == 'Tag1') {
                tagVariance.Tag1 += pow(genes[i][j].x - tagCenterX.Tag1, 2) + pow(genes[i][j].y - tagCenterY.Tag1, 2);
            }
            if (dataset[j].tags[0][3] == 'Tag2' || dataset[j].tags[1][3] == 'Tag2' || dataset[j].tags[2][3] == 'Tag2') {
                tagVariance.Tag2 += pow(genes[i][j].x - tagCenterX.Tag2, 2) + pow(genes[i][j].y - tagCenterY.Tag2, 2);
            }
            if (dataset[j].tags[0][3] == 'Tag3' || dataset[j].tags[1][3] == 'Tag3' || dataset[j].tags[2][3] == 'Tag3') {
                tagVariance.Tag3 += pow(genes[i][j].x - tagCenterX.Tag3, 2) + pow(genes[i][j].y - tagCenterY.Tag3, 2);
            }
            if (dataset[j].tags[0][3] == 'Tag4' || dataset[j].tags[1][3] == 'Tag4' || dataset[j].tags[2][3] == 'Tag4') {
                tagVariance.Tag4 += pow(genes[i][j].x - tagCenterX.Tag4, 2) + pow(genes[i][j].y - tagCenterY.Tag4, 2);
            }
            if (dataset[j].tags[0][3] == 'Tag5' || dataset[j].tags[1][3] == 'Tag5' || dataset[j].tags[2][3] == 'Tag5') {
                tagVariance.Tag5 += pow(genes[i][j].x - tagCenterX.Tag5, 2) + pow(genes[i][j].y - tagCenterY.Tag5, 2);
            }
        }
        //計算結果の確認
        printf("Individual %d: Tag1 Variance = %f, Tag2 Variance = %f, Tag3 Variance = %f, Tag4 Variance = %f, Tag5 Variance = %f\n", i, tagVariance.Tag1, tagVariance.Tag2, tagVariance.Tag3, tagVariance.Tag4, tagVariance.Tag5);
        //３．適応度は分散の合計
        fitness[i] = tagVariance.Tag1 + tagVariance.Tag2 + tagVariance.Tag3 + tagVariance.Tag4 + tagVariance.Tag5;
    }
    
}