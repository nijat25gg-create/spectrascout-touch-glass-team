"""Generate contracts/schemas/*.schema.json from models.py. Run after every change to models.py."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from models import CONTRACTS, SCHEMA_VERSION

NAMES = {"C1": "analyze_request", "C2": "extract_input", "C3": "extraction", "C4": "score_input",
         "C5": "scoring", "C6": "explain_input", "C7": "explanation", "C8": "briefing",
         "C1b": "recompute_request", "E": "error_response"}

out = pathlib.Path(__file__).parent / "schemas"
out.mkdir(exist_ok=True)
for cid, model in CONTRACTS.items():
    schema = model.model_json_schema()
    schema["$id"] = f"spectrascout/{SCHEMA_VERSION}/{cid}"
    path = out / f"{cid}_{NAMES[cid]}.schema.json"
    path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", path.name)
