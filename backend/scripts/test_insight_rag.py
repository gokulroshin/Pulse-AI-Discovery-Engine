import urllib.request
import json
import sys

# Force utf-8 stdout on windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

questions = [
    "Why do customers complain about fabric transparency in ethnic dresses?",
    "What do customers say about courier delivery delays and tracking?",
    "Why do users add fashion products to their wishlist?"
]

for q in questions:
    payload = json.dumps({"question": q}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/insights/ask",
        data=payload,
        headers={"Content-Type": "application/json", "X-API-Key": "pulse-secret-key-123"}
    )
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode("utf-8"))
        print("\n" + "="*70, flush=True)
        print(f"QUESTION: {data['question']}", flush=True)
        print(f"EXECUTIVE SUMMARY:\n{data['summary']}", flush=True)
        print(f"KEY DRIVERS ({len(data['key_drivers'])} items):", flush=True)
        for d in data['key_drivers']:
            print(f"  - {d}", flush=True)
        print(f"SUPPORTING EVIDENCE ({len(data['supporting_evidence'])} quotes):", flush=True)
        for ev in data['supporting_evidence'][:2]:
            print(f"  [{ev['source_platform'].upper()}] \"{ev['verbatim_quote'][:100]}...\"", flush=True)
        print(f"LINKED OPPORTUNITIES: {[o['label'] for o in data['linked_opportunities'][:2]]}", flush=True)
    except Exception as e:
        print(f"Error on '{q}':", e, flush=True)
