import re
import numpy as np
from ranges import clinical_ranges


def analyze_report(text):
    results = []
    for param, (low, high) in clinical_ranges.items():
        match = re.search(param + r".*?(\d+\.?\d*)", text, re.IGNORECASE)
        if match:
            value = float(match.group(1))

            # Logic for Status
            if value < low:
                status = "Low"
            elif value > high:
                status = "High"
            else:
                status = "Normal"

            # NEW: Severity Score (How far from the mid-point?)
            mid_point = (low + high) / 2
            # Using numpy to calculate percentage deviation
            deviation = np.abs(value - mid_point) / (high - low) * 100
            results.append({
                "Parameter": param,
                "Value": value,
                "Normal Range": f"{low}-{high}",
                "Status": status,
                "Severity_Score": round(deviation, 2)
            })
    return results