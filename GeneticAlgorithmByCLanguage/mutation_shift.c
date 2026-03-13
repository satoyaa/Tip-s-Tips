#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "extern.h"
#include "collision.h"

//TIPの位置をずらす突然変異，エリート保存あり，0番目の個体がエリート
//突然変異率に基づいて，適当なTIPを選択
//選択されたTIPのX座標とY座標をランダムにずらす
//ずらす量は-50,-40,-30,-20,-10, 0, 10,20,30,40,50からランダムに生成
//ずらした後に重複判定を行い，重複する場合は再度乱数生成してずらす
//また，領域外にはみ出ないかも確認する0<x<maxWidth-tipWidth, 0<y
//5回ずらしても重複する場合は諦める
void mutation_shift(){
    for(int i=1;i < POPULATION;i++){
        if((rand()/(double)RAND_MAX) < mutation_shift_rate){
            // 0からmax_tips-1の乱数
            int tip_index = rand() % max_tips;
            int shift_valuesX[] = {-50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50};
            int shift_valuesY[] = {-300, -250, -200, -150, -100, -50, -10, 0};
            int shift_indexX = rand() % (sizeof(shift_valuesX)/sizeof(shift_valuesX[0]));
            int shift_indexY = rand() % (sizeof(shift_valuesY)/sizeof(shift_valuesY[0]));
            double shift_x = shift_valuesX[shift_indexX];
            double shift_y = shift_valuesY[shift_indexY];
            
            int attempts = 0;
            while(attempts < 5){
                int shift_indexX = rand() % (sizeof(shift_valuesX)/sizeof(shift_valuesX[0]));
                int shift_indexY = rand() % (sizeof(shift_valuesY)/sizeof(shift_valuesY[0]));
                double shift_x = shift_valuesX[shift_indexX];
                double shift_y = shift_valuesY[shift_indexY];
                double new_x = genes[i][tip_index].x + shift_x;
                double new_y = genes[i][tip_index].y + shift_y;
                
                // 重複判定 rectsOverlap関数を使用して、new_x, new_yが他のTIPと重複していないか確認
                int duplicate = 0;
                for (int k = 0; k < max_tips; k++)
                {
                    if (k != tip_index && rectsOverlap(new_x, new_y, dataset[tip_index].rotate,
                                                        genes[i][k].x, genes[i][k].y, dataset[k].rotate))
                    {
                        duplicate = 1;
                        break;
                    }
                }
                if(new_x < 0 || new_x > maxWidth - tipWidth || new_y < 0 || new_y > maxWidth - tipHeight){
                    duplicate = 1; // はみ出しも重複と同様に扱う
                }
                if(!duplicate){
                    genes[i][tip_index].x = new_x;
                    genes[i][tip_index].y = new_y;
                    break;
                }
                //はみ出し判定
                
                attempts++;
            }
        }
    }
}