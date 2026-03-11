#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "extern.h"
#include "collision.h"

//交換突然変異，エリート保存あり，0番目の個体がエリート
void mutation(){
    for (int i = 0; i < POPULATION; i++)
    {
        TIPS elite_genes[max_tips];
        //エリート保存
        if (i == 0)
        {
            for (int j = 0; j < max_tips; j++)
            {
                elite_genes[j] = genes[i][j];
            }
        }
        if (rand() / (double)RAND_MAX < mutation_rate) {
            int idx1 = rand() % max_tips;
            int idx2 = rand() % max_tips;
            // 交換
            TIPS temp = genes[i][idx1];
            genes[i][idx1] = genes[i][idx2];
            genes[i][idx2] = temp;
            //重複判定
            //重複する場合は再度乱数生成   
            //10回試行しても重複する場合は諦める 
            
            int flag;
            for (int i = 0; i < 10; i++)
            {
                flag = 1;
                for (int j = 0; j < max_tips; j++)
                {
                    //衝突判定
                    if (j != idx1 && j != idx2 && rectsOverlap(genes[i][idx1].x, genes[i][idx1].y, dataset[idx1].rotate,
                                                                genes[i][j].x, genes[i][j].y, dataset[j].rotate))
                    {
                        // 重複する場合は再度乱数生成
                        int newIdx1 = rand() % max_tips;
                        int newIdx2 = rand() % max_tips;
                        // 交換
                        TIPS temp = genes[i][newIdx1];
                        genes[i][newIdx1] = genes[i][newIdx2];
                        genes[i][newIdx2] = temp;
                        flag = 0;
                        break;
                    }
                    if(j != idx1 && j != idx2 && rectsOverlap(genes[i][idx2].x, genes[i][idx2].y, dataset[idx2].rotate,
                                                                genes[i][j].x, genes[i][j].y, dataset[j].rotate))
                    {
                        // 重複する場合は再度乱数生成
                        int newIdx1 = rand() % max_tips;
                        int newIdx2 = rand() % max_tips;
                        // 交換
                        TIPS temp = genes[i][newIdx1];
                        genes[i][newIdx1] = genes[i][newIdx2];
                        genes[i][newIdx2] = temp;
                        flag = 0;
                        break;
                    }
                }
                if (flag)
                {
                    break;
                }
            }
            //10回試行しても重複する場合は諦める
            if(!flag){
                // 元に戻す
                TIPS temp = genes[i][idx1];
                genes[i][idx1] = genes[i][idx2];
                genes[i][idx2] = temp;
            }
        }
        //エリート保存        
        if (i == 0)
        {
            for (int j = 0; j < max_tips; j++)
            {
                genes[i][j] = elite_genes[j];
            }
        }
    }
    
}