import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import glob

# ロギングの初期設定
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class BaseAnalyzer:
    """分析用クラスの基底（ベース）クラス。"""
    @property
    def name(self) -> str:
        raise NotImplementedError

    def process_data(self, data: dict):
        raise NotImplementedError

    def report(self):
        raise NotImplementedError

class DateRangeAnalyzer(BaseAnalyzer):
    """最初と最後の日記の日付を特定するアナライザー"""
    def __init__(self):
        self.min_date = None
        self.max_date = None

    @property
    def name(self) -> str:
        return "date_range"

    def process_data(self, data: dict):
        date_str = data.get("dateOfJournal")
        if not date_str:
            return
        try:
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            dt = datetime.fromisoformat(date_str).astimezone()
            if self.min_date is None or dt < self.min_date:
                self.min_date = dt
            if self.max_date is None or dt > self.max_date:
                self.max_date = dt
        except ValueError:
            pass

    def report(self):
        min_dt = self.min_date.isoformat() if self.min_date else 'なし'
        max_dt = self.max_date.isoformat() if self.max_date else 'なし'
        print(f"最初の日記 : {min_dt}")
        print(f"最後の日記 : {max_dt}")

class TimeGroupCountAnalyzer(BaseAnalyzer):
    """期間ごとの日記件数を集計するアナライザー"""
    def __init__(self, unit="month"):
        self.counts = defaultdict(int)
        self.unit = unit  # "year", "month", "day" から指定

    @property
    def name(self) -> str:
        return f"time_count ({self.unit})"

    def process_data(self, data: dict):
        date_str = data.get("dateOfJournal")
        if not date_str:
            return
        try:
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            dt = datetime.fromisoformat(date_str).astimezone()
            
            # 指定された単位で文字列キーを作成
            if self.unit == "year":
                key = dt.strftime("%Y")
            elif self.unit == "month":
                key = dt.strftime("%Y-%m")
            elif self.unit == "day":
                key = dt.strftime("%Y-%m-%d")
            else:
                key = dt.strftime("%Y-%m")
                
            self.counts[key] += 1
        except ValueError:
            pass

    def report(self):
        unit_label = {"year": "年", "month": "月", "day": "日"}.get(self.unit, "期間")
        print(f"{unit_label}ごとの件数:")
        if self.counts:
            for key in sorted(self.counts.keys()):
                print(f"  {key} : {self.counts[key]} 件")
        else:
            print("  データなし")

# ====== 分析の種類を追加する場合は、上記のようにクラスを作り、以下の辞書に登録します ======
# 辞書の値は「CLIで渡された args を引数に取って、アナライザーのインスタンスを返す関数」にします
AVAILABLE_ANALYZERS = {
    "date_range": lambda args: DateRangeAnalyzer(),
    # time_count に改名し、引数から集計単位を生成時に渡すようにしました
    "time_count": lambda args: TimeGroupCountAnalyzer(unit=args.time_unit),
}
# ==============================================================================

class JourneyEngine:
    """JSONの読み込みと、登録された各アナライザーの実行を統合管理するエンジンクラス"""
    def __init__(self, analyzers: list[BaseAnalyzer]):
        self.analyzers = analyzers
        self.processed_files = 0
        self.error_files = 0

    def process_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for analyzer in self.analyzers:
                analyzer.process_data(data)
                
            self.processed_files += 1
        except json.JSONDecodeError:
            logger.debug(f"JSONパースエラー: {file_path}")
            self.error_files += 1
        except Exception as e:
            logger.debug(f"ファイル処理エラー ({file_path}): {e}")
            self.error_files += 1

    def run_report(self):
        print("=" * 40)
        print("Journey JSON 分析レポート")
        print("=" * 40)
        print(f"処理完了ファイル数 : {self.processed_files}")
        print(f"スキップ/エラー数  : {self.error_files}")
        
        for analyzer in self.analyzers:
            print("-" * 40)
            print(f"【 分析: {analyzer.name} 】")
            analyzer.report()
        print("=" * 40)

def main():
    parser = argparse.ArgumentParser(
        description="指定したフォルダ配下のJourney JSONファイルを分析します。"
    )
    # パス引数
    parser.add_argument(
        "directories", 
        nargs="+",
        type=str, 
        help="JSONファイルが格納されている対象フォルダのパス（複数指定・ワイルドカード対応）"
    )
    
    # 分析種類の引数
    analyzer_choices = list(AVAILABLE_ANALYZERS.keys())
    parser.add_argument(
        "--analyzers", "-a",
        nargs="+",
        choices=analyzer_choices,
        default=analyzer_choices,
        help=f"実行する分析処理の名前（複数指定可）。{analyzer_choices} から選択。指定しない場合は全て実行されます。"
    )
    
    # 集計単位の引数
    parser.add_argument(
        "--time-unit",
        choices=["year", "month", "day"],
        default="month",
        help="time_count アナライザーでの集計単位を指定します（デフォルト: month）"
    )
    
    # その他のオプション引数
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="詳細なログを出力します"
    )

    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    target_dirs = []
    for d in args.directories:
        matches = glob.glob(d)
        if not matches:
            logger.warning(f"パスが見つかりません（スキップします）: {d}")
            continue
        
        for match in matches:
            p = Path(match)
            if p.is_dir():
                target_dirs.append(p)
            else:
                logger.warning(f"フォルダではありません（スキップします）: {match}")

    if not target_dirs:
        logger.error("有効な対象フォルダが1つも見つかりませんでした。")
        return

    # 選択されたアナライザーを初期化してエンジンにセット (ラムダ式に args を渡す)
    active_analyzers = [AVAILABLE_ANALYZERS[name](args) for name in args.analyzers]
    engine = JourneyEngine(active_analyzers)

    json_files = []
    for d in target_dirs:
        json_files.extend(list(d.rglob("*.json")))
        
    logger.info(f"対象フォルダからJSONファイルを合計 {len(json_files)} 件見つけました。分析を開始します...")

    for file_path in json_files:
        engine.process_file(file_path)

    engine.run_report()

if __name__ == "__main__":
    main()
