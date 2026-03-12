import ctypes
import random
import time

# 1. Cの構造体に対応するクラスを定義
class DataPoint(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("tags", (ctypes.c_char * 10) * 3),  # char tags[3][10]
        ("rotate", ctypes.c_double)
    ]

# 2. ライブラリ読み込み
lib = ctypes.CDLL('./libGA.dll')
lib.ga_main.argtypes = [ctypes.POINTER(DataPoint), ctypes.c_int]

def generate_test_data(n):
    # DataPoint はあらかじめ定義されている前提です
    data_array = (DataPoint * n)()

    for i in range(n):
        data_array[i].x = 0.0
        data_array[i].y = 0.0
        data_array[i].rotate = float(random.randint(-10, 10))

        # --- タグ生成ロジック ---
        r_vals = [random.randint(1, 5) for _ in range(3)]
        
        # tag1, tag2, tag3 を決定
        t1 = f"Tag{r_vals[0]}".encode('utf-8')
        
        # 重複チェックのロジック
        t2 = b"Tag0"
        if i % 3 >= 1: # 2つ以上の場合
            if r_vals[1] != r_vals[0]:
                t2 = f"Tag{r_vals[1]}".encode('utf-8')
                
        t3 = b"Tag0"
        if i % 3 == 2: # 3つの場合
            if r_vals[2] != r_vals[0] and r_vals[2] != r_vals[1]:
                t3 = f"Tag{r_vals[2]}".encode('utf-8')

        # --- 重要：[:] を使って固定長配列の中身を更新 ---
        # これにより TypeError: expected c_char_Array_... を回避できます
        data_array[i].tags[0][:] = t1.ljust(len(data_array[i].tags[0]), b'\0')
        data_array[i].tags[1][:] = t2.ljust(len(data_array[i].tags[1]), b'\0')
        data_array[i].tags[2][:] = t3.ljust(len(data_array[i].tags[2]), b'\0')

    return data_array

# 4. データの準備
n = 25
data_array = generate_test_data(n)
tag_list = ["焼き方", "ゆで方", "煮詰め方", "揚げ方", "切り方", "味付け"]
num_tags = len(tag_list)

# 2. C言語の型「char[10]」と「char[要素数][10]」を定義
# 長さ10の文字配列型
TagString10 = ctypes.c_char * 64
# 長さ10の文字配列が num_tags 個集まった2次元配列型
TagListType = TagString10 * num_tags 

# 3. Pythonのリストから ctypes の配列インスタンスを作成
# ※ C言語に渡すため、文字列はエンコードしてバイト列（b"Tag0"など）にする必要があります
c_tag_array = TagListType()
# 修正後 (正しく代入される)
for i, tag in enumerate(tag_list):
    c_tag_array[i].value = tag.encode('utf-8')

# テストデータの出力（先頭5件）
print("Before Processing n:")
for i in range(n):
    tags = [bytes(data_array[i].tags[j]).rstrip(b"\x00").decode('utf-8') for j in range(3)]
    print(f"Item[{i}]: Tags = {{{tags[0]}, {tags[1]}, {tags[2]}}}, rotate={data_array[i].rotate}")

# 5. 実行
start = time.perf_counter()
lib.ga_main(data_array, n, c_tag_array, num_tags)
end = time.perf_counter()
# 5. 結果（座標のみ更新されているか確認）
for i in range(n):
    print(f"Python-side: Updated Data[{i}] ({data_array[i].x}, {data_array[i].y})")

print(f"aの処理時間：{end-start}")