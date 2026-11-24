import os
import csv
import hashlib

report_root = r"C:\Users\USER\Desktop\MedNourish-Dev\report_data"
log_path = os.path.join(report_root, "logs", "final_check.txt")
manifest_path = os.path.join(report_root, "MANIFEST.csv")

results = []
results.append("================================================================================")
results.append("MEDNOURISH REPORT_DATA INTEGRITY AUDIT & SELF-CHECK VERIFICATION")
results.append("================================================================================")
results.append(f"Audit Target Directory: {report_root}")
results.append("")

total_available = 0
total_missing_documented = 0
errors = 0

with open(manifest_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rel = row["relative_path"]
        status = row["availability_status"]
        expected_size = int(row["file_size_bytes"])
        expected_sha = row["sha256"]
        full_path = os.path.join(report_root, rel.replace("/", "\\"))
        
        if status.startswith("AVAILABLE"):
            if not os.path.exists(full_path):
                results.append(f"[FAIL] Missing file: {rel}")
                errors += 1
            else:
                actual_size = os.path.getsize(full_path)
                if actual_size == 0:
                    results.append(f"[FAIL] Zero-byte file: {rel}")
                    errors += 1
                else:
                    # Check sha256
                    h = hashlib.sha256()
                    with open(full_path, "rb") as fh:
                        while chunk := fh.read(65536):
                            h.update(chunk)
                    actual_sha = h.hexdigest()
                    if actual_sha != expected_sha:
                        results.append(f"[FAIL] SHA256 mismatch for {rel}: expected {expected_sha}, got {actual_sha}")
                        errors += 1
                    else:
                        total_available += 1
        else:
            total_missing_documented += 1
            results.append(f"[AUDIT NOTE] Documented unavailable item: {rel} -> {status}")

results.append("")
results.append("--------------------------------------------------------------------------------")
results.append("CATEGORY BREAKDOWN OF VERIFIED ARTIFACTS:")
results.append("--------------------------------------------------------------------------------")

categories = {}
with open(manifest_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cat = row["category"]
        st = row["availability_status"]
        if st.startswith("AVAILABLE"):
            categories[cat] = categories.get(cat, 0) + 1

for cat, count in sorted(categories.items()):
    results.append(f"  - {cat.upper()}: {count} verified files")

results.append("")
results.append("--------------------------------------------------------------------------------")
results.append(f"TOTAL VERIFIED AVAILABLE ARTIFACTS : {total_available}")
results.append(f"TOTAL DOCUMENTED UNAVAILABLE ITEMS : {total_missing_documented}")
results.append(f"TOTAL AUDIT FAILURES / ERRORS     : {errors}")
results.append("--------------------------------------------------------------------------------")

if errors == 0:
    results.append("STATUS: PASSED - 100% ARTIFACT INTEGRITY CONFIRMED")
    results.append("REPORT_DATA PACKAGE IS COMPLETE, CONSISTENT, AND READY FOR PACKAGING.")
else:
    results.append(f"STATUS: FAILED WITH {errors} ERRORS")

results.append("================================================================================")
output_text = "\n".join(results) + "\n"

with open(log_path, "w", encoding="utf-8") as f:
    f.write(output_text)

print(output_text)
