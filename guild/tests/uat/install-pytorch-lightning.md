---
doctest: -PY2 -PY310 # 2022-04-26 torch 1.10 is not available for python 3.10. We should bump the constraint to 1.11 when time allows.
---

# Install PyTorch Lightning

    >>> quiet("pip install pytorch-lightning==1.5.4", timeout=120)

    >>> quiet("pip install torchvision==0.11.1", timeout=120)
