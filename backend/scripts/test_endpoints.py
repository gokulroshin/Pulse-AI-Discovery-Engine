import json
import urllib.request

def test_opportunities():
    print("--- 1. Testing GET /api/v1/opportunities ---")
    req = urllib.request.Request("http://localhost:8000/api/v1/opportunities")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"Total Opportunities: {data['total_opportunities']}")
        for opp in data["opportunities"]:
            print(f"  #{opp['rank']} [{opp['composite_score']:.2f}] {opp['label']} (Extractions: {opp['extraction_count']})")

def test_insight(question: str):
    print(f"\n--- 2. Testing POST /api/v1/insights/ask: \"{question}\" ---")
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/insights/ask",
        data=json.dumps({"question": question}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"Summary: {data['summary']}\n")
        print("Linked Opportunities:")
        for opp in data.get("linked_opportunities", []):
            print(f"  - #{opp['rank']} {opp['label']} ({opp['composite_score']:.2f})")
        print("\nCorroborating Evidence Quotes:")
        for i, ev in enumerate(data.get("supporting_evidence", []), 1):
            q_clean = ev['verbatim_quote'].encode('ascii', 'replace').decode('ascii')
            r_clean = ev['reason_text'].encode('ascii', 'replace').decode('ascii')
            print(f"  [{i}] ({ev['source_platform'].upper()}) \"{q_clean}\"")
            print(f"      Context: {r_clean}")

if __name__ == "__main__":
    test_opportunities()
    test_insight("What prevents wishlisted products from eventually being purchased?")
    test_insight("Why do users add fashion products to their wishlist?")
    test_insight("What uncertainties remain after users have identified a product they like?")
