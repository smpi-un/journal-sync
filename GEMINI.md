# Gemini開発ノウハウ

このドキュメントは、Geminiとの対話を通じて実装およびデバッグを行う過程で得られた技術的な知見やノウハウを記録します。

## 1. Pythonスクリプトの実行とモジュール解決

### 問題
プロジェクトのルートディレクトリ外（例: `utils/`）にあるスクリプトから、`src/`ディレクトリ内のモジュールをインポートしようとすると`ModuleNotFoundError`が発生する。

- `utils/script.py` 内の `from src.components.my_module import ...` が失敗する。
- `src`内のモジュール間での相対インポート（例: `from journal_core import ...`）も、実行コンテキストによっては失敗する。

### 解決策
コード自体を修正するのではなく、スクリプトの**実行環境**を調整することで、インポートパスの競合を解決します。`PYTHONPATH`環境変数に、プロジェクトルート (`.`) と `src` ディレクトリの両方をコロン(`:`)で区切って設定します。

```bash
PYTHONPATH=.:src uv run path/to/your/script.py
```

- **`PYTHONPATH=.`**: `from src. ...` という形式のインポートを解決できるようにします。
- **`PYTHONPATH=src`**: `src`ディレクトリ内のモジュールが `from journal_core ...` のように、`src`をルートとして相互にインポートできるようにします。

この方法により、異なる実行コンテキストでも動作する、より堅牢な実行が可能になります。

## 2. Payload CMSへの添付ファイル付きエントリー登録

### 課題
新規の日記エントリーと、それに紐づくローカルの添付ファイル（画像など）を同時にPayload CMSへ登録する。

### 実装戦略
PayloadのAPIでは、エントリー作成とファイルアップロードは別々のエンドポイントです。そのため、以下の手順で処理を実装しました。

1.  **先にファイルをアップロード**: 新規エントリーに紐づくローカルファイルを先にすべて`files`コレクションにアップロードします。
2.  **ファイルIDの取得**: アップロードが成功すると、Payloadは各ファイルに一意のIDを返します。これらのIDをリストに保存します。
3.  **エントリーの作成**: テキストデータなどの本体情報と、ステップ2で取得したファイルIDのリストを使って`journals`コレクションにエントリーを作成します。ペイロードの`attachments`フィールドには、`[{"file": "ID1"}, {"file": "ID2"}, ...]` のような形式で指定します。

この手順は、`src/clients/payload_client.py`の`register_entry`メソッドに実装されています。

## 3. Pillowライブラリによる画像処理の注意点

### 問題1: 特定画像のフォーマットが認識されない
一部の画像（特にインメモリのバイトデータから開いた場合）で、画像処理ライブラリPillowが`image.format`を`None`と返し、これが原因で後続処理（特に`save`メソッド）で`'NoneType' object has no attribute 'startswith'`のような予期せぬエラーを発生させることがあります。

### 解決策
`image.format`が`None`だった場合のフォールバック処理を追加します。ファイル名（拡張子）から画像フォーマットを推定し、手動で設定します。

```python
# in convert_to_webp()
with Image.open(io.BytesIO(image_bytes)) as img:
    original_format = img.format
    if not original_format:
        file_ext = pathlib.Path(original_filename).suffix.lower()
        if file_ext in [".jpg", ".jpeg"]:
            original_format = "JPEG"
        elif file_ext == ".png":
            original_format = "PNG"
```

### 問題2: EXIFデータのない画像でのエラー
PNG画像など、EXIFデータを持たない画像に対して`save`メソッドで`exif=None`を渡そうとすると、Pillowの内部でエラーが発生することがあります。

### 解決策
`save`メソッドの引数を動的に構築します。EXIFデータが`None`でない場合にのみ、`exif`引数を渡すようにします。

```python
# in convert_to_webp()
exif_data = img.info.get("exif")
save_kwargs = {
    "format": "WEBP",
    "quality": 85,
}
if exif_data:
    save_kwargs["exif"] = exif_data

img.save(output_buffer, **save_kwargs)
```

## 4. Gitコミットのベストプラクティス

### 基本フロー
1.  **変更内容の確認**: `git status`で変更・追加されたファイルの一覧を確認し、`git diff HEAD`で具体的な変更内容を精査します。
2.  **ステージング**: `git add <file1> <file2> ...` でコミット対象のファイルを選択します。一時ファイル（例: コミットメッセージの下書きファイル）はステージングしません。
3.  **ログスタイルの確認**: `git log -n 5`などで過去のコミットメッセージを閲覧し、件名や本文の書き方、言語、粒度などのスタイルを把握・踏襲します。
4.  **コミットメッセージの作成**:
    - **件名(Subject)**: 変更内容の要約を英語の命令形で記述します。（例: `feat: Add image processing feature`）
    - **本文(Body)**:
        - **Why**: なぜこの変更が必要だったのか（目的、背景、修正したバグなど）。
        - **What**: 何を変更したのか（新機能の概要、主要な修正点など）。
        - これらを明確に記述します。
5.  **コミットの実行**: `git commit -m "..."` または、詳細なメッセージの場合は `-F <file>` を使ってコミットします。
