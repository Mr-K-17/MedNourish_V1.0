import os
import sys

BASE_DIRS = [
    r"C:\Users\USER\Desktop\MedNourish-Dev\backend\app",
    r"C:\Users\USER\Desktop\MedNourish-Dev\frontend\src",
]

BANNED_STRINGS = [
    "autonomous diagnosis",
    "clinical decision support system",
    "we prescribe",
    "cure your",
    "replaces your doctor",
]

def scan_files():
    found_violations = []
    total_files = 0

    for base_dir in BASE_DIRS:
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith((".py", ".tsx", ".ts")):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        for banned in BANNED_STRINGS:
                            if banned in content:
                                found_violations.append((file_path, banned))

    print(f"Scanned {total_files} source files.")
    if found_violations:
        print(f"FAILED: Found {len(found_violations)} forbidden string occurrences:")
        for path, banned in found_violations:
            print(f"  {path} -> '{banned}'")
        sys.exit(1)
    else:
        print("SUCCESS: Zero prohibited diagnostic or prescriptive claims detected across all source files.")

if __name__ == "__main__":
    scan_files()
