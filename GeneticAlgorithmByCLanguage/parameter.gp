# 軸ラベル
set xlabel "Mutation rate"
set ylabel "Crossover rate"
set zlabel "Best fitness"

# 対数軸（画像のような 0.001,0.01,0.1,1 表示）
set logscale x
set format x "10^{%L}"

# 見た目
set grid
set hidden3d
set ticslevel 0

# 視点
set view 60, 35

# 凡例なし
set key off

# プロット
splot "parameterTest.dat" using 1:2:3 with lines lc rgb "blue"