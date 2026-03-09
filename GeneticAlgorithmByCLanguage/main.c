#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "extern.h"

TIPS genes[POPULATION][MAX_TIPS]; 
DataItem dataset[50];
double fitness[POPULATION];
double best;
int best_index = 0;
int maxWidth = 1280;
int tipWidth = 220;
int tipHeight = 180;



void ga(){
    initialize();
    calc_fitness();
    for(int i=0;i < MAX_ITERATION;i++){
        selection();          // トーナメント選択
        crossover();          // PMX交叉
        mutation();           // 反転交叉
        calc_fitness();// 適応度計算
    }
    // 現世代の最良個体を算出
    for (int j = 0; j < POPULATION; j++) {
        if (fitness[j] < best) {
            best = fitness[j];
        }
    }
    //printf("best:%f\n",best);
}

int main(){

    

    // 2. データの初期化（テスト用ダミーデータ 50件）
    for (int i = 0; i < 50; i++) {
        dataset[i].x = 0.0;
        dataset[i].y = 0.0;
        dataset[i].rotate = (rand()%20-10);

        // タグの生成例：
        // データごとに「1」「2」「3」の可変長を模擬
        if (i % 3 == 0) { // タグ1つの場合
            strcpy(dataset[i].tags[0], "Tag1");
            strcpy(dataset[i].tags[1], "Tag0");
            strcpy(dataset[i].tags[2], "Tag0");
        } else if (i % 3 == 1) { // タグ2つの場合
            strcpy(dataset[i].tags[0], "Tag2");
            strcpy(dataset[i].tags[1], "Tag4");
            strcpy(dataset[i].tags[2], "Tag0");
        } else { // タグ3つの場合
            strcpy(dataset[i].tags[0], "Tag1");
            strcpy(dataset[i].tags[1], "Tag3");
            strcpy(dataset[i].tags[2], "Tag5");
        }
    }

    printf("Before Processing (First 5):\n");
    for (int i = 0; i < 5; i++) {
        printf("Item[%d]: Tags = {%s, %s, %s}\n", i, dataset[i].tags[0], dataset[i].tags[1], dataset[i].tags[2]);
    }
    //initialize();のテスト
    initialize();

    /*
    printf("After Initialization (First 5 Individuals):\n");
    for (int i = 0; i < 5; i++) {
        printf("Individual[%d]: ", i);
        for (int j = 0; j < MAX_TIPS; j++) {
            if (genes[i][j].x != -1 && genes[i][j].y != -1) {
                printf("(x: %.2f, y: %.2f) ", genes[i][j].x, genes[i][j].y);
            }
        }
        printf("\n");
    }*/

    // データ読み込みプログラムのテスト
    // dataset[i].rotate は genes[best_index][i] の回転量 (°)
    save("data.dat");
    calc_fitness();

    //ga();
    return 0;
}