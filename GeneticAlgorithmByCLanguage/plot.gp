# 1. 出力形式の設定 (PNG形式、サイズ、フォント)
set terminal pngcairo size 800, 800 font "Arial,12"
set output "output.png"

# 2. グラフの見た目の設定
set xrange [0:1280]
set yrange [0:2000]
set style fill solid 0.7 border lt -1
set key off
set size ratio -1

# 3. 描画実行
# index 0: ポリゴンを描画 (using 1:2:3 -> x:y:color)
# index 1: ラベルを描画 (using 1:2:3 -> x:y:"label_text")
plot "data.dat" index 0 using 1:2:3 with polygons lc rgb variable, \
     "data.dat" index 1 using 1:2:3 with labels font "Arial,14" textcolor rgb "black"