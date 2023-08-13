# 環境構築

1. pythonをインストール
    - [ここから](https://www.python.org/)
2. 仮想環境作成
    ```bash
    python -m venv --upgrade-deps .env
    ```
3. 仮想環境に入る
    - windows
        ```bash
        .env\Scripts\activate
        ```
    - mac/linux
        ```bash
        source .env/bin/activate
        ```
4. ライブラリインストール
    ```bash
    pip install -r setting/requirements.txt
    ```
5. 実行
    ```bash
    python text_translate.py
    ```
    - ツールの使い方は**doc/readme.pdf**を確認
    - 翻訳対象のファイルは**dataフォルダ**以下に格納している