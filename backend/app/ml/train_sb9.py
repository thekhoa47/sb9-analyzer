# app/ml/train_sb9.py
import argparse
from pathlib import Path
from .sb9_model import fit

### Run this for training:
# python -m app.ml.train_sb9 --data ~/sb9-training-data
#
### OR this to save different version
# python -m app.ml.train_sb9 --data ~/sb9-training-data --out app/models/sb9_v2.pt

def str2bool(v: str) -> bool:
    return str(v).lower() in {"1", "true", "t", "yes", "y"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="folder with class subfolders (YES/NO)")
    ap.add_argument("--out", default="app/models/sb9_v1.pt", help="path to save the model artifact")
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--patience", type=int, default=8)
    # NEW: control freezing the backbone (default True)
    ap.add_argument("--freeze-backbone", type=str2bool, default=True,
                    help="Freeze feature extractor and train classifier head only (default: True)")
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
        freeze_backbone=args.freeze_backbone,  # <-- forward to fit()
    )

if __name__ == "__main__":
    main()
