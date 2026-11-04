import joblib
import os

# Original model
original_path = "model/etawise_bts_model_bundle.joblib"

# Compressed model
compressed_path = "model/etawise_bts_model_compressed.joblib"

print("Loading original model...")
bundle = joblib.load(original_path)

print("\nOriginal model components:")
for key in bundle:
    print(" -", key)

# Keep only components required for the selected model
essential_keys = [
    "selected_name",
    "distance_trend",
    "residual_forest",
    "features",
    "uses_calibrated_road_distance",
    "target",
    "target_unit",
    "train_mean_hours",
    "random_seed",
]

compressed_bundle = {
    key: bundle[key]
    for key in essential_keys
    if key in bundle
}

print("\nCompressing model...")

joblib.dump(
    compressed_bundle,
    compressed_path,
    compress=9
)

original_size = os.path.getsize(original_path) / (1024**2)
compressed_size = os.path.getsize(compressed_path) / (1024**2)

print(f"\nOriginal size: {original_size:.2f} MB")
print(f"Compressed size: {compressed_size:.2f} MB")
print(f"Reduction: {(1 - compressed_size / original_size) * 100:.1f}%")

print("\nCompression completed!")