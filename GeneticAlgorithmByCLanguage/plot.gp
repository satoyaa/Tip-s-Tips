# 1. 出力形式の設定 (PNG形式、サイズ、フォント)
set terminal pngcairo size 800, 800 font "Arial,12"
set output "output.png"

# 2. グラフの見た目の設定
set xrange [0:1280]
set yrange [0:2000]
set style fill solid 0.7 border lt -1
set key off

# 描画実行
# using 1:2:3 -> x:y:color
# lc rgb variable -> 3列目の値をRGB色として使用
plot "data.dat" using 1:2:3 with polygons lc rgb variable