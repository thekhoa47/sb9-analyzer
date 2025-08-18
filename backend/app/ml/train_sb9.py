# app/ml/train_sb9.py
import argparse
from pathlib import Path
from .sb9_model import fit

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="folder with class subfolders (ELIGIBLE/INELIGIBLE)")
    ap.add_argument("--out", default="app/models/sb9_v1.pt", help="path to save the model artifact")
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--patience", type=int, default=4)
    args = ap.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fit(
        data_dir=args.data,
        out_path=args.out,
        epochs=args.epochs,
        lr=args.lr,
        wd=args.wd,
        batch_size=args.batch_size,
        patience=args.patience,
    )

if __name__ == "__main__":
    main()
