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

int main(){

    max_tips = 25; // データの数を設定
    // 2. データの初期化（テスト用ダミーデータ MAX_TIPS件）
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
            int r1 = rand() % 5 + 1; // 1から5の乱数
            sprintf(str1, "Tag%d", r1);
            strcpy(dataset[i].tags[0], str1);
            strcpy(dataset[i].tags[1], "Tag0");
            strcpy(dataset[i].tags[2], "Tag0");
        } else if (i % 3 == 1) { // タグ2つの場合
            int r1 = rand() % 5 + 1; // 1から5の乱数
            sprintf(str1, "Tag%d", r1);
            strcpy(dataset[i].tags[0], str1);
            int r2 = rand() % 5 + 1; // 1から5の乱数
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
            int r1 = rand() % 5 + 1; // 1から5の乱数
            sprintf(str1, "Tag%d", r1);
            strcpy(dataset[i].tags[0], str1);
            int r2 = rand() % 5 + 1; // 1から5の乱数
            if(r1==r2){
                //同じタグが選ばれたTag0をセット
                strcpy(dataset[i].tags[1], "Tag0");
                strcpy(dataset[i].tags[2], "Tag0");
            }else{
                sprintf(str2, "Tag%d", r2);
                strcpy(dataset[i].tags[1], str2);
                int r3 = rand() % 5 + 1; // 1から5の乱数
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
    for (int i = 0; i < MAX_TIPS; i++) {
        printf("Item[%d]: Tags = {%s, %s, %s}\n", i, dataset[i].tags[0], dataset[i].tags[1], dataset[i].tags[2]);
    }

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
    // GAのパラメータ調整結果をファイル出力（parameter.dat）
    FILE *fp = fopen("parameter.dat", "w");
    if (fp == NULL) {
        perror("fopen(parameter.dat)");
        return 1;
    }
    fprintf(fp, "交叉率 突然変異率 平均最良評価値 最良評価値分散 平均実行時間 実行時間分散\n");

    double crossover_rates[] = {0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0};
    double mutation_rates[] = {0.0, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0};
    double best_crossover_rate = 0.0;
    double best_mutation_rate = 0.0;
    double best_fitness = INFINITY;
    double best_fitnesses[LOOPS];
    double best_fitness_sum;
    double best_fitness_avg;
    double best_fitness_variance;
    double times[LOOPS];
    double time_sum;
    double time_avg;
    double time_variance;
    int start_time;
    int end_time;
    double elapsed_time;

    
    for (int i = 0; i < 11; i++)
    {
        for (int j = 0; j < 11; j++)
        {
            crossover_rate = crossover_rates[i];
            mutation_rate = mutation_rates[j];
            printf("Crossover Rate: %.2f, Mutation Rate: %.3f\n", crossover_rate, mutation_rate);
            best_fitness_sum = 0.0;
            time_sum = 0.0;
            best_fitness_variance = 0.0;
            time_variance = 0.0;
            for (int k = 0; k < LOOPS; k++)
            {
                start_time = clock();
                ga();
                end_time = clock();
                elapsed_time = (double)(end_time - start_time) / CLOCKS_PER_SEC;
                best_fitness_sum += best;
                time_sum += elapsed_time;
                best_fitnesses[k] = best;
                times[k] = elapsed_time;
            }
            best_fitness_avg = best_fitness_sum / LOOPS;
            time_avg = time_sum / LOOPS;
            best_fitness_variance = 0.0;
            time_variance = 0.0;
            for (int k = 0; k < LOOPS; k++)
            {
                best_fitness_variance += pow(best_fitnesses[k] - best_fitness_avg, 2);
                time_variance += pow(times[k] - time_avg, 2);
            }
            // 分散
            best_fitness_variance /= LOOPS;
            time_variance /= LOOPS;

            if (best_fitness_avg < best_fitness)
            {
                best_fitness = best_fitness_avg;
                best_crossover_rate = crossover_rate;
                best_mutation_rate = mutation_rate;
            }

            fprintf(fp, "%.2f %.3f %.6f %.6f %.6f %.6f\n",
                    crossover_rate,
                    mutation_rate,
                    best_fitness_avg,
                    best_fitness_variance,
                    time_avg,
                    time_variance);
        }
    }
    

    
    printf("Best parameters: crossover=%.2f mutation=%.3f (avg best fitness=%.6f)\n",
           best_crossover_rate, best_mutation_rate, best_fitness);
    fclose(fp);
    /*
    printf("Fitness of first 5 individuals after selection:\n");
    for (int i = 0; i < 5; i++) {
        printf("Individual[%d]: Fitness = %f\n", i, fitness[i]);
    }*/
    return 0;
}