import os
import zipfile
import json
import shutil
import argparse  # コマンドライン引数を処理するために追加
from collections import defaultdict

def unzip_and_update_json(zip_file_path, output_dir):
    """
    zipファイルを指定されたディレクトリに解凍し、
    各サブディレクトリのjsonファイルに添付ファイルリストを追記する。
    添付ファイルの順序はzipファイルのエントリ順に従う。
    """
    
    if not os.path.exists(zip_file_path):
        print(f"エラー: zipファイルが見つかりません: {zip_file_path}")
        return

    # 出力先ディレクトリが既存の場合は削除してクリーンアップ
    if os.path.exists(output_dir):
        # ユーザーに上書き確認（あるいはオプションで制御）するのが親切だが、
        # 今回は元の仕様通り、既存の場合は削除する
        print(f"警告: 既存の出力先ディレクトリ '{output_dir}' を削除します。")
        try:
            shutil.rmtree(output_dir)
        except OSError as e:
            print(f"エラー: ディレクトリの削除に失敗しました: {e}")
            return

    # 出力先ディレクトリを作成
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"出力先ディレクトリ '{output_dir}' を作成/使用します。")
    except OSError as e:
        print(f"エラー: 出力先ディレクトリの作成に失敗しました: {e}")
        return

    # フォルダごとにファイル情報を格納する辞書
    # defaultdict を使い、キーが存在しない場合に自動的に
    # {"json_file": None, "attachments": []} を作成するように設定
    folders_data = defaultdict(lambda: {"json_file": None, "attachments": []})

    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            
            print(f"'{zip_file_path}' を読み込んでいます...")
            
            # 1. zipファイル内のエントリ順 (infolist()) でループ
            #    これが「zipに追加した順序」となる
            file_info_list = zip_ref.infolist()
            
            for info in file_info_list:
                # ディレクトリ自体はスキップ
                if info.is_dir():
                    continue
                
                # ファイルパスをフォルダ名とファイル名に分割
                try:
                    # 'XtrZa4ljuJ17n5KmDbAA/29VJSV3NYAjQqDCPd8fY.png' ->
                    # folder_name = 'XtrZa4ljuJ17n5KmDbAA'
                    # file_name = '29VJSV3NYAjQqDCPd8fY.png'
                    
                    # OS非依存のパス分割 (zip標準の '/' 区切りを想定)
                    parts = info.filename.split('/')
                    if len(parts) > 1:
                        folder_name = parts[0]
                        file_name = parts[-1]
                    else:
                        # ルートディレクトリのファイル
                        folder_name = ""
                        file_name = parts[0]

                except Exception:
                    print(f"警告: パス形式が無効です。スキップします: {info.filename}")
                    continue

                # ルートディレクトリのファイルはスキップ (今回の要件ではフォルダ内のみ)
                if not folder_name:
                    continue
                
                # ファイル名が空の場合もスキップ (例: 'folder/')
                if not file_name:
                    continue

                # 拡張子でjsonか添付ファイルかを判断
                if file_name.endswith('.json'):
                    # zip内のフルパスを格納
                    folders_data[folder_name]["json_file"] = info.filename
                else:
                    # 添付ファイルの場合、ファイル名 (basename) のみをリストに追加
                    # infolist() の順序で append される
                    folders_data[folder_name]["attachments"].append(file_name)
            
            # 2. すべてのファイルを一括解凍 (フォルダ構造は維持される)
            print(f"'{output_dir}' へ解凍中...")
            zip_ref.extractall(output_dir)
            print("解凍が完了しました。")

            # 3. 解凍したjsonファイルを更新
            print("JSONファイルの更新処理を開始します...")
            updated_count = 0
            
            for folder_name, data in folders_data.items():
                if data["json_file"]:
                    # 解凍後のjsonファイルのフルパス
                    # (os.path.join はOSのパス区切り文字を使うため、
                    # output_dir と zip内のパス info.filename を安全に結合できる)
                    json_full_path = os.path.join(output_dir, data["json_file"])
                    
                    try:
                        # jsonファイルを読み込む
                        with open(json_full_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                        
                        # "attachments" キーに、収集したファイル名のリスト（順序維持）を追加
                        json_data["attachments"] = data["attachments"]
                        
                        # jsonファイルに上書き保存
                        with open(json_full_path, 'w', encoding='utf-8') as f:
                            # ensure_ascii=False で日本語をそのまま出力
                            # indent=2 で見やすくフォーマット
                            json.dump(json_data, f, ensure_ascii=False, indent=2)
                        
                        print(f"  更新完了: {data['json_file']} (添付 {len(data['attachments'])} 件)")
                        updated_count += 1
                        
                    except json.JSONDecodeError:
                        print(f"  エラー: JSONの読み込みに失敗しました: {json_full_path}")
                    except IOError as e:
                        print(f"  エラー: ファイルの読み書きに失敗しました: {json_full_path} ({e})")
                    except Exception as e:
                        print(f"  予期せぬエラー: {json_full_path} ({e})")
                else:
                    print(f"  警告: フォルダ '{folder_name}' にjsonファイルが見つかりませんでした。")

            print(f"処理完了。{updated_count} 件のJSONファイルを更新しました。")

    except zipfile.BadZipFile:
        print(f"エラー: '{zip_file_path}' は有効なzipファイルではありません。")
    except FileNotFoundError:
        print(f"エラー: 指定されたファイルが見つかりません: {zip_file_path}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    # --- コマンドライン引数の設定 ---
    parser = argparse.ArgumentParser(
        description="ZIPファイルを解凍し、指定されたフォルダ構造内のJSONファイルに添付ファイルリスト（ZIP内の順序）を追記します。"
    )
    
    # 必須の引数: 1. zipファイルのパス
    parser.add_argument(
        "zip_file_path", 
        type=str,
        help="処理対象のZIPファイルのパス"
    )
    
    # 必須の引数: 2. 出力先のディレクトリパス
    parser.add_argument(
        "output_dir",
        type=str,
        help="解凍先のディレクトリパス（存在しない場合は作成されます）"
    )
    
    # 引数を解析
    args = parser.parse_args()
    
    print("--- 解凍ツールの実行 ---")
    
    # メイン処理を実行
    unzip_and_update_json(args.zip_file_path, args.output_dir)