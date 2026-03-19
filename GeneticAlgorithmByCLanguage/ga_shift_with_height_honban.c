#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <time.h>

#include "extern.h"

TIPS genes[POPULATION][MAX_TIPS]; 
DataItem dataset[50];
double fitness[POPULATION];
double best;
int best_index = 0;
int maxWidth = 1280;
int tipWidth = 257;
int tipHeight = 257;
double crossover_rate = 0.1;
double mutation_rate = 0.5;
double mutation_shift_rate = 0.3;
int max_tips;
int num_tags;
char Taglist[100][64];

void ga(){
    best = INFINITY; // 最良個体の適応度を初期化
    initialize();
    calc_fitness_with_height();
    for(int i=0;i < MAX_ITERATION;i++){
        selection();          // トーナメント選択
        crossover();          // 1点交叉
        mutation();           // 交換突然変異
        mutation_shift();     // TIPの位置をずらす突然変異
        calc_fitness_with_height();// 適応度計算
    }
    // 現世代の最良個体を算出
    for (int j = 0; j < POPULATION; j++) {
        if (fitness[j] < best) {
            best = fitness[j];
        }
    }
}

int ga_main(DataItem* dataset, int n, char tagList[100][64], int num_tags) {
    max_tips = n; // データの数を設定
    //reset_ga_state(); // GAの状態をリセット
    ga();
    //datasetの中身を最良個体に置き換える
    //datasetの中身を最良個体に置き換える
    for (int j = 0; j < max_tips; j++) {
        if (genes[0][j].x != -1 && genes[0][j].y != -1) {
            dataset[j].x = genes[0][j].x+cos(dataset[j].rotate * M_PI / 180.0)*5+sin(dataset[j].rotate * M_PI / 180.0)*5;
            dataset[j].y = genes[0][j].y+sin(dataset[j].rotate * M_PI / 180.0)*5-cos(dataset[j].rotate * M_PI / 180.0)*5;
        }
    }
    return 0;
}