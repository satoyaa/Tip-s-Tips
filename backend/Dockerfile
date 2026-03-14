# 1. 軽量な公式Pythonイメージをベースに使用
FROM python:3.11-slim

# 2. コンテナ内の作業ディレクトリを設定
WORKDIR /backend

# 3. 依存関係のファイルを「先に」コピー
COPY requirements.txt .

# 4. パッケージのインストール
# --no-cache-dir をつけることで、不要なキャッシュファイルを残さずイメージを軽量化
RUN pip install --no-cache-dir -r requirements.txt

# 5. アプリケーションのソースコード全体をコピー
COPY . .

# 6. コンテナ起動時に実行されるコマンド（FastAPIをUvicornで起動）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]