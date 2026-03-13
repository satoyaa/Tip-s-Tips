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
double mutation_shift_rate = 0.2;
int max_tips;

char Taglist[100][64] = {"Tag0", "Tag1", "Tag2", "Tag3", "Tag4", "Tag5"};
int num_tags = 6; // タグの数を設定（Tag1～Tag5）


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

int main(){

    max_tips = 25; // データの数を設定

    // 2. テスト用ダミーデータ max_tips件
    for (int i = 0; i < max_tips; i++) {
        dataset[i].x = 0.0;
        dataset[i].y = 0.0;
        dataset[i].rotate = (rand()%20-10);
        char str1[10];
        char str2[10];
        char str3[10];

        // タグの生成例：
        // データごとに「1」「2」「3」の可変長を模擬
        if (i % 3 == 0) { // タグ1つの場合
            int r1 = rand() % num_tags + 1; // 1から5の乱数
            sprintf(str1, "Tag%d", r1);
            strcpy(dataset[i].tags[0], str1);
            strcpy(dataset[i].tags[1], "Tag0");
            strcpy(dataset[i].tags[2], "Tag0");
        } else if (i % 3 == 1) { // タグ2つの場合
            int r1 = rand() % num_tags + 1; // 1から5の乱数
            sprintf(str1, "Tag%d", r1);
            strcpy(dataset[i].tags[0], str1);
            int r2 = rand() % num_tags + 1; // 1から5の乱数
            if(r1==r2){
                //同じタグが選ばれたTag0をセット
                strcpy(dataset[i].tags[1], "Tag0");
                strcpy(dataset[i].tags[2], "Tag0");
            }else{
                sprintf(str2, "Tag%d", r2);
                strcpy(dataset[i].tags[1], str2);
                strcpy(dataset[i].tags[2], "Tag0");
            }
        } else { // タグ3つの場合
            int r1 = rand() % num_tags + 1; // 1から5の乱数
            sprintf(str1, "Tag%d", r1);
            strcpy(dataset[i].tags[0], str1);
            int r2 = rand() % num_tags + 1; // 1から5の乱数
            if(r1==r2){
                //同じタグが選ばれたTag0をセット
                strcpy(dataset[i].tags[1], "Tag0");
                strcpy(dataset[i].tags[2], "Tag0");
            }else{
                sprintf(str2, "Tag%d", r2);
                strcpy(dataset[i].tags[1], str2);
                int r3 = rand() % num_tags + 1; // 1から5の乱数
                if(r1==r3 || r2==r3){
                    //同じタグが選ばれたTag0をセット
                    strcpy(dataset[i].tags[2], "Tag0");
                }else{
                    sprintf(str3, "Tag%d", r3);
                    strcpy(dataset[i].tags[2], str3);
                }
            }
        }
    }

    printf("Before Processing (First 5):\n");
    for (int i = 0; i < max_tips; i++) {
        printf("Item[%d]: Tags = {%s, %s, %s}\n", i, dataset[i].tags[0], dataset[i].tags[1], dataset[i].tags[2]);
    }
    
    ga();
    save("data.dat");
    /*
    printf("Fitness of first 5 individuals after selection:\n");
    for (int i = 0; i < 5; i++) {
        printf("Individual[%d]: Fitness = %f\n", i, fitness[i]);
    }*/
    return 0;
}