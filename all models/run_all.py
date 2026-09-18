"""
run_all.py

Small runner to automate the FinBERT-LSTM pipeline. It copies data files into the
expected locations, optionally runs news collection, then runs cleaning,
sentiment and the chosen model(s).

Usage examples:
  python run_all.py --collect-news            # run collection, cleaning, sentiment, bert model
  python run_all.py --models mlp lstm        # run only MLP and LSTM models
  python run_all.py --skip-sentiment         # skip sentiment step

This script is intentionally conservative: it won't overwrite existing CSVs
unless --force is provided.
"""
import argparse
import os
import shutil
import subprocess
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))
RESEARCH_STOCK = os.path.join(ROOT, "research", "stock")


def ensure_research_dirs():
    if not os.path.exists(RESEARCH_STOCK):
        os.makedirs(RESEARCH_STOCK, exist_ok=True)


def copy_if_present(src_name, dest_dir, force=False):
    src = os.path.join(ROOT, src_name)
    dest = os.path.join(dest_dir, src_name)
    if os.path.exists(dest) and not force:
        print(f"[skip] {dest} already exists")
        return
    if os.path.exists(src):
        shutil.copy2(src, dest)
        print(f"[copied] {src} -> {dest}")
    else:
        print(f"[missing] {src} (not copied)")


def run_script(script_name):
    script_path = os.path.join(ROOT, script_name)
    if not os.path.exists(script_path):
        print(f"[error] Script not found: {script_path}")
        return False
    print(f"[run] {script_name}")
    try:
        subprocess.run([sys.executable, script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[fail] {script_name} exited with {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run FinBERT-LSTM pipeline")
    parser.add_argument("--collect-news", action="store_true", help="Run 1_news_collection.py to fetch news")
    parser.add_argument("--use-gdelt", action="store_true", help="Use GDELT fetcher to produce news.csv in research/stock")
    parser.add_argument("--gdelt-start", help="GDELT start date YYYY-MM-DD")
    parser.add_argument("--gdelt-end", help="GDELT end date YYYY-MM-DD")
    parser.add_argument("--gdelt-max", type=int, default=10, help="Max headlines per day for GDELT")
    parser.add_argument("--skip-cleaning", action="store_true", help="Skip the cleaning step (3_news_data_cleaning.py)")
    parser.add_argument("--skip-sentiment", action="store_true", help="Skip sentiment analysis (4_news_sentiment_analysis.py)")
    parser.add_argument("--models", nargs="*", 
                       choices=["mlp", "mlp_fixed", "lstm", "bert", "bert_fixed", "advanced", "ensemble", "all"], 
                       help="Which models to run (default: advanced). Use 'all' to run advanced, mlp_fixed, and ensemble")
    parser.add_argument("--force", action="store_true", help="Overwrite destination CSVs when copying")
    args = parser.parse_args()

    ensure_research_dirs()

    # Copy root CSVs into research/stock if present
    copy_if_present("news.csv", RESEARCH_STOCK, force=args.force)
    copy_if_present("stock_price.csv", RESEARCH_STOCK, force=args.force)

    # Optionally run news collection
    if args.collect_news:
        ok = run_script("1_news_collection.py")
        if not ok:
            print("Stopping due to failure in news collection")
            sys.exit(1)
        # copy newly created news.csv into research/stock
        copy_if_present("news.csv", RESEARCH_STOCK, force=True)

    # Optionally use GDELT to create a news CSV in research/stock
    if args.use_gdelt:
        gdelt_start = args.gdelt_start or ""
        gdelt_end = args.gdelt_end or ""
        if not gdelt_start or not gdelt_end:
            print("--use-gdelt requires --gdelt-start and --gdelt-end (YYYY-MM-DD).")
            sys.exit(1)
        out_path = os.path.join(RESEARCH_STOCK, "news.csv")
        gdelt_args = [
            "--start",
            gdelt_start,
            "--end",
            gdelt_end,
            "--out",
            out_path,
            "--checkpoint",
            os.path.join(ROOT, "gdelt_checkpoint.json"),
            "--max",
            str(args.gdelt_max),
            "--resume",
        ]

        # run with full python executable
        script_path = os.path.join(ROOT, "gdelt_fetch.py")
        cmd = [sys.executable, script_path] + gdelt_args
        print(f"[run] gdelt_fetch.py {' '.join(gdelt_args)}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[fail] gdelt_fetch.py exited with {e.returncode}")
            sys.exit(1)

    # Cleaning step
    if not args.skip_cleaning:
        ok = run_script("3_news_data_cleaning.py")
        if not ok:
            print("Stopping due to failure in cleaning")
            sys.exit(1)

    # Sentiment step
    if not args.skip_sentiment:
        ok = run_script("4_news_sentiment_analysis.py")
        if not ok:
            print("Stopping due to failure in sentiment analysis")
            sys.exit(1)

    # Models to run
    models = args.models or ["advanced"]
    for m in models:
        if m == "mlp":
            ok = run_script("5_MLP_model.py")
        elif m == "mlp_fixed":
            ok = run_script("5_MLP_model_FIXED.py")
        elif m == "lstm":
            ok = run_script("6_LSTM_model.py")
        elif m == "bert":
            ok = run_script("7_lstm_model_bert.py")
        elif m == "bert_fixed":
            ok = run_script("7_lstm_model_bert_FIXED.py")
        elif m == "advanced":
            ok = run_script("8_advanced_model.py")
        elif m == "ensemble":
            ok = run_script("9_ensemble_model.py")
        elif m == "all":
            # Run all models
            print("[info] Running all models...")
            for model_script in ["8_advanced_model.py", "5_MLP_model_FIXED.py", "9_ensemble_model.py"]:
                ok = run_script(model_script)
                if not ok:
                    print(f"Stopping due to failure in {model_script}")
                    sys.exit(1)
            continue
        else:
            print(f"[warning] Unknown model: {m}, skipping")
            ok = True
        if not ok:
            print(f"Stopping due to failure while running model: {m}")
            sys.exit(1)

    print("All requested steps completed.")


if __name__ == "__main__":
    main()
