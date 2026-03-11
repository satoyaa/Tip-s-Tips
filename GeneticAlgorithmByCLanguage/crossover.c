#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "extern.h"
#include "collision.h"

// onepoint crossover，エリート保存付き，0番目の個体がエリート
void crossover(){
    for (int i = 0; i < POPULATION; i++)
    {
        if (i==0)
        {
            continue;
        }
        
        if (rand() / (double)RAND_MAX < crossover_rate) {
            int partner = rand() % POPULATION;
            int crossoverPoint = rand() % max_tips;
            TIPS tempGenes[max_tips];
            for (int j = 0; j < crossoverPoint; j++) {
                tempGenes[j] = genes[i][j];
            }
            for (int j = crossoverPoint; j < max_tips; j++) {
                tempGenes[j] = genes[partner][j];
            }
            //衝突判定
            //衝突した場合は置換しない
            int flag = 1;
            for (int j = 0; j < max_tips; j++){
                for (int k = 0; k < max_tips; k++){
                    if (rectsOverlap(tempGenes[j].x, tempGenes[j].y, dataset[j].rotate,
                                     genes[i][k].x, genes[i][k].y, dataset[k].rotate))
                    {
                        flag = 0;
                        break;
                    }
                }
                if (!flag) {
                    break;
                }
            }
            if (flag) {
                for (int j = 0; j < max_tips; j++) {
                    genes[i][j] = tempGenes[j];
                }
            }
        }   
    }
}