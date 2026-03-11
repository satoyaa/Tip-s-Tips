#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "extern.h"

void selection(){
    //トーナメント選択，エリート保存付き
    TIPS newGenes[POPULATION][max_tips];
    
    for (int i = 0; i < POPULATION; i++)
    {
        //最良個体を保存するために，best_indexを決める
        if (fitness[i] < best) {
            best = fitness[i];
            best_index = i;
        }
        int idx1 = rand() % POPULATION;
        int idx2 = rand() % POPULATION;
        int selected = (fitness[idx1] < fitness[idx2]) ? idx1 : idx2;
        for (int j = 0; j < max_tips; j++){
            newGenes[i][j] = genes[selected][j];
        }
    }
    //エリート保存
    for (int i = 0; i < max_tips; i++){
        newGenes[0][i] = genes[best_index][i];
    }
    //新しい世代に置き換え
    for (int i = 0; i < POPULATION; i++)
    {
        for (int j = 0; j < max_tips; j++)
        {
            genes[i][j] = newGenes[i][j];
        }
    }
}