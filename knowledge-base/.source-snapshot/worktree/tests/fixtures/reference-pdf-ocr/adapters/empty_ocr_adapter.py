import argparse
import json


parser = argparse.ArgumentParser()
parser.add_argument("--source")
parser.add_argument("--page", type=int)
parser.add_argument("--output")
parser.add_argument("--schema-version", type=int)
parser.add_argument("--cancel-file")
arguments = parser.parse_args()
payload = {
    "schema_version": arguments.schema_version,
    "status": "extracted",
    "page_number": arguments.page,
    "text": "",
    "confidence": 0.99,
    "engine": {"name": "empty-output-fixture", "version": "1"},
    "detection_count": 0,
}
with open(arguments.output, "w", encoding="utf-8", newline="\n") as stream:
    json.dump(payload, stream, ensure_ascii=False, sort_keys=True)
    stream.write("\n")
