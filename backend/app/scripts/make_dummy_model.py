# scripts/make_dummy_sb9.py
import os
import time
import torch
import torch.nn as nn
from torchvision import models

OUT_PATH = "app/models/sb9_v1.pt"

# 2-class MobileNetV3-Small (classes: ELIGIBLE, INELIGIBLE)
num_classes = 2
class_to_idx = {"ELIGIBLE": 0, "INELIGIBLE": 1}

m = models.mobilenet_v3_small(weights=None)  # no pretrained needed for dummy
in_feats = m.classifier[-1].in_features
m.classifier[-1] = nn.Linear(in_feats, num_classes)

artifact = {
    "state_dict": m.state_dict(),
    "class_to_idx": class_to_idx,
    "input_size": 224,
    "mean": [0.485, 0.456, 0.406],
    "std": [0.229, 0.224, 0.225],
    "model_name": "mobilenet_v3_small",
    "version": "v0-dummy",
    "created_at": time.time(),
}

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
torch.save(artifact, OUT_PATH)
print(f"✅ Wrote dummy SB9 artifact to: {OUT_PATH}")
