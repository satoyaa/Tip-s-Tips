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
int tipWidth = 247;
int tipHeight = 176;
double crossover_rate = 0.1;
double mutation_rate = 0.5;
int max_tips;
int num_tags;
char Taglist[100][64];

void reset_ga_state() {
    // 1. 配列のゼロクリア
    // sizeof(配列名) とすることで、配列全体のサイズ分を確実に 0 で埋めます。
    memset(genes, 0, sizeof(genes));
    memset(dataset, 0, sizeof(dataset));
    memset(fitness, 0, sizeof(fitness));
    memset(Taglist, 0, sizeof(Taglist));

    // 2. スカラー変数のリセット（ご提示の初期値に合わせる）
    best_index = 0;
    maxWidth = 1280;
    tipWidth = 247;
    tipHeight = 176;
    crossover_rate = 0.1;
    mutation_rate = 0.5;
    
    // 3. 初期値の指定がない変数のリセット
    best = 0.0;       // ※GAの評価関数が負の値を取る場合は、適切な初期値（例えば -9999.0 等）に変更してください
    max_tips = 0;
    num_tags = 0;
}

void ga(){
    best = INFINITY; // 最良個体の適応度を初期化
    initialize();
    calc_fitness();
    for(int i=0;i < MAX_ITERATION;i++){
        selection();          // トーナメント選択
        crossover();          // 1点交叉
        mutation();           // 交換突然変異
        calc_fitness();// 適応度計算
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
    reset_ga_state(); // GAの状態をリセット
    ga();
    //datasetの中身を最良個体に置き換える
    for (int j = 0; j < max_tips; j++) {
        if (genes[0][j].x != -1 && genes[0][j].y != -1) {
            dataset[j].x = genes[0][j].x;
            dataset[j].y = genes[0][j].y;
        }
    }
    return 0;
}