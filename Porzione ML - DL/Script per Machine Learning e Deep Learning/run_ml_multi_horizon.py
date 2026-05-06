import subprocess
import sys

PYTHON_EXEC = sys.executable

horizons = [1, 6, 12, 24]

for h in horizons:

    print("\n" + "="*60)
    print(f"TRAINING HORIZON T+{h}")
    print("="*60)

    subprocess.run([
        PYTHON_EXEC,
        "train_ml_models_all_targets.py",
        f"--horizon={h}"
    ])
