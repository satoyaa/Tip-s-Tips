#ifndef COLLISION_H
#define COLLISION_H

#ifdef __cplusplus
extern "C" {
#endif

// 回転矩形（幅 tipWidth、高さ tipHeight）の衝突判定
//  - x,y: 左上座標
//  - rotate: 回転角度（°）
// 返り値: 衝突していれば 1, していなければ 0
int rectsOverlap(double x1, double y1, double rotate1,
                 double x2, double y2, double rotate2);

#ifdef __cplusplus
}
#endif

#endif // COLLISION_H
