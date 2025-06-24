import os
import json
import matplotlib.pyplot as plt


def show_usage_dashboard():
    if not os.path.exists("usage_stats.json"):
        print("📭 No usage stats available.")
        return

    with open("usage_stats.json", "r", encoding="utf-8") as f:
        stats = json.load(f)

    labels = ["Messages Sent", "Files Sent", "Data Sent (KB)"]
    values = [
        stats.get("messages_sent", 0),
        stats.get("files_sent", 0),
        stats.get("data_sent_kb", 0)
    ]

    plt.figure(figsize=(8, 4))
    plt.bar(labels, values)
    plt.title("📊 Usage Dashboard")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show()
