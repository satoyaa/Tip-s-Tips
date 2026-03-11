#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "extern.h"
#include "collision.h"

void initialize(){
    //配列初期化
    for (int i = 0; i < POPULATION; i++)
    {
        for (int j = 0; j < MAX_TIPS; j++)
        {
            //使わないtipはx,yともに-1とするため，初期値は-1とする
            genes[i][j].x = -1;
            genes[i][j].y = -1;
        }   
    }
    for (int i = 0; i < POPULATION; i++)
    {
        int currentMaxHeight = tipHeight;
        for (int j = 0; j < max_tips; j++)
        {
            int x = rand()%(maxWidth-tipWidth);
            int y = rand()%(currentMaxHeight);
            //tip同士が重ならないか判定
            //tipはx,y,x+幅，y+高さの四角形とみなす
            //tipの高さと幅はすべての同じとする
            //重なる場合は再度乱数生成
            int counter = 0;
            while (1)
            {
                int flag = 1;
                counter++;
                if(counter > 10){
                    //10回試行しても重複する場合はy座標を最大高さ+tipHeightにしてみる
                    y = currentMaxHeight+tipHeight;
                    currentMaxHeight = y + tipHeight;
                    counter = 0;    
                }
                for (int k = 0; k < max_tips; k++)
                {
                    //未定義のtip
                    if (genes[i][k].x == -1 && genes[i][k].y == -1)
                    {
                        break;
                    }
                            // 回転後の座標で重なり判定
                    if (rectsOverlap(x, y, dataset[j].rotate,
                                     genes[i][k].x, genes[i][k].y, dataset[k].rotate))
                    {
                        // 重なる場合は再度乱数生成
                        x = rand()%(maxWidth-tipWidth);
                        y = rand()%(currentMaxHeight);
                        flag = 0;
                        break;
                    }

                }
                if(flag){
                    break;
                }
            }
            genes[i][j].x = x;
            genes[i][j].y = y;
            currentMaxHeight = (currentMaxHeight > y + tipHeight) ? currentMaxHeight : y + tipHeight;
        }
    }
}