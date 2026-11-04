from pathlib import Path
import joblib

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "model"
    / "etawise_bts_model_bundle.joblib"
)

print("Checking model:", MODEL_PATH)

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

bundle = joblib.load(MODEL_PATH)

print("\nModel loaded successfully!")
print("Bundle type:", type(bundle).__name__)

if isinstance(bundle, dict):
    print("\nAvailable bundle keys:")
    for key in bundle:
        print(" -", key)

    print("\nContents:")
    for key, value in bundle.items():
        print(f"{key}: {type(value).__name__}")