# app/ml/sb9_model.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List, Optional
from io import BytesIO
import json
import time
import math
import requests
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import models, transforms, datasets
from PIL import Image


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]
INPUT_SIZE = 224


@dataclass
class SB9Artifact:
    state_dict: Dict[str, Any]
    class_to_idx: Dict[str, int]
    input_size: int
    mean: List[float]
    std: List[float]
    model_name: str
    version: str  # e.g., "v1"
    created_at: float

    def to_file(self, path: str):
        torch.save({
            "state_dict": self.state_dict,
            "class_to_idx": self.class_to_idx,
            "input_size": self.input_size,
            "mean": self.mean,
            "std": self.std,
            "model_name": self.model_name,
            "version": self.version,
            "created_at": self.created_at,
        }, path)

    @staticmethod
    def from_file(path: str, map_location: Optional[str] = None) -> "SB9Artifact":
        payload = torch.load(path, map_location=map_location or "cpu")
        return SB9Artifact(
            state_dict=payload["state_dict"],
            class_to_idx=payload["class_to_idx"],
            input_size=payload.get("input_size", INPUT_SIZE),
            mean=payload.get("mean", IMAGENET_MEAN),
            std=payload.get("std", IMAGENET_STD),
            model_name=payload.get("model_name", "mobilenet_v3_small"),
            version=payload.get("version", "v1"),
            created_at=payload.get("created_at", time.time()),
        )


def create_model(num_classes: int, pretrained: bool = True) -> nn.Module:
    m = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None)
    in_feats = m.classifier[-1].in_features
    m.classifier[-1] = nn.Linear(in_feats, num_classes)
    return m


def default_transforms(train: bool) -> transforms.Compose:
    if train:
        return transforms.Compose([
            transforms.RandomResizedCrop(INPUT_SIZE, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(0.1, 0.1, 0.1, 0.05),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])
    else:
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])


def make_loaders_from_folder(
    data_dir: str,
    batch_size: int = 16,
    num_workers: int = 2,
    val_split: float = 0.2,
    seed: int = 42,
) -> Tuple[DataLoader, DataLoader, Dict[str, int]]:
    """
    Expects folder structure:
      data_dir/
        ELIGIBLE/
          *.png|jpg
        INELIGIBLE/
          *.png|jpg
    """
    full_ds = datasets.ImageFolder(data_dir, transform=None)  # defer transforms
    class_to_idx = full_ds.class_to_idx

    # stratified split
    from sklearn.model_selection import train_test_split
    y = [full_ds.targets[i] for i in range(len(full_ds))]
    idx = list(range(len(full_ds)))
    train_idx, val_idx = train_test_split(idx, test_size=val_split, stratify=y, random_state=seed)

    # subset datasets with transforms
    train_ds = torch.utils.data.Subset(
        datasets.ImageFolder(data_dir, transform=default_transforms(train=True)),
        train_idx
    )
    val_ds = torch.utils.data.Subset(
        datasets.ImageFolder(data_dir, transform=default_transforms(train=False)),
        val_idx
    )

    # class weights (handle imbalance with ~200 images)
    import numpy as np
    train_targets = np.array([full_ds.targets[i] for i in train_idx])
    class_sample_count = np.bincount(train_targets, minlength=len(class_to_idx))
    weights = 1.0 / np.maximum(class_sample_count, 1)
    samples_weight = weights[train_targets]
    sampler = WeightedRandomSampler(torch.from_numpy(samples_weight).double(), num_samples=len(samples_weight), replacement=True)

    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)
    return train_loader, val_loader, class_to_idx


def train_one_epoch(model, loader, criterion, optimizer, device) -> Tuple[float, float]:
    model.train()
    running_loss, correct, total = 0.0, 0, 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        running_loss += float(loss.item()) * images.size(0)
        pred = logits.argmax(1)
        correct += int((pred == labels).sum().item())
        total += images.size(0)

    return running_loss / max(total, 1), correct / max(total, 1)


@torch.no_grad()
def evaluate(model, loader, criterion, device) -> Tuple[float, float]:
    model.eval()
    running_loss, correct, total = 0.0, 0, 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        logits = model(images)
        loss = criterion(logits, labels)

        running_loss += float(loss.item()) * images.size(0)
        pred = logits.argmax(1)
        correct += int((pred == labels).sum().item())
        total += images.size(0)
    return running_loss / max(total, 1), correct / max(total, 1)


def fit(
    data_dir: str,
    out_path: str,
    epochs: int = 12,
    lr: float = 3e-4,
    wd: float = 1e-4,
    batch_size: int = 16,
    patience: int = 4,
    device: Optional[str] = None,
) -> SB9Artifact:
    train_loader, val_loader, class_to_idx = make_loaders_from_folder(data_dir, batch_size=batch_size)
    device = device or ("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))

    model = create_model(num_classes=len(class_to_idx), pretrained=True).to(device)
    # unfreeze everything (mobilenet is small). For even smaller dataset, you can freeze backbone first.
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    criterion = nn.CrossEntropyLoss()

    best_acc, best_state = 0.0, None
    bad_epochs = 0

    for epoch in range(1, epochs + 1):
        tr_loss, tr_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        va_loss, va_acc = evaluate(model, val_loader, criterion, device)
        print(f"[{epoch:02d}] train loss {tr_loss:.4f} acc {tr_acc:.3f} | val loss {va_loss:.4f} acc {va_acc:.3f}")

        if va_acc > best_acc:
            best_acc = va_acc
            best_state = model.state_dict()
            bad_epochs = 0
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                print(f"Early stopping at epoch {epoch} (best val acc {best_acc:.3f}).")
                break

    # fall back to final weights if best_state somehow None
    final_state = best_state or model.state_dict()
    artifact = SB9Artifact(
        state_dict=final_state,
        class_to_idx=class_to_idx,
        input_size=INPUT_SIZE,
        mean=IMAGENET_MEAN,
        std=IMAGENET_STD,
        model_name="mobilenet_v3_small",
        version="v1",
        created_at=time.time(),
    )
    artifact.to_file(out_path)
    print(f"Saved model to {out_path}")
    return artifact


# -------- Inference helpers (for your FastAPI) --------

class SB9Runner:
    def __init__(self, artifact_path: str, device: Optional[str] = None):
        self.artifact_path = artifact_path
        self.device = device or ("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))
        self.art = SB9Artifact.from_file(artifact_path, map_location=self.device)
        self.model = create_model(num_classes=len(self.art.class_to_idx), pretrained=False).to(self.device)
        self.model.load_state_dict(self.art.state_dict)
        self.model.eval()
        self.idx_to_class = {v: k for k, v in self.art.class_to_idx.items()}
        self.tx = default_transforms(train=False)

    @torch.no_grad()
    def predict_pil(self, img: Image.Image) -> Tuple[str, float, Dict[str, float]]:
        img = img.convert("RGB")
        tens = self.tx(img).unsqueeze(0).to(self.device)
        logits = self.model(tens)
        prob = torch.softmax(logits, dim=1)[0]
        conf, idx = float(prob.max().item()), int(prob.argmax().item())
        label = self.idx_to_class[idx]
        probs = {self.idx_to_class[i]: float(prob[i].item()) for i in range(len(prob))}
        return label, conf, probs

    @torch.no_grad()
    def predict_from_url(self, url: str) -> Tuple[str, float, Dict[str, float]]:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
        return self.predict_pil(img)
