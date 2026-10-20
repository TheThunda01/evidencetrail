"""Build a synthetic audit ZIP and print its byte-consistency verification."""
from hashlib import sha256
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evidencetrail.audit import audit_table
from evidencetrail.bundle import verify_bundle
from evidencetrail.io import load_table
from evidencetrail.progress import evidence_completeness,review_progress
from evidencetrail.reports import audit_bundle

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python scripts/bundle_example.py NEW_OUTPUT.zip')
    raw=(ROOT/'examples/demo_records.csv').read_bytes();frame=load_table('demo_records.csv',raw)
    bundle=audit_bundle(audit_table(frame),{'filename':'demo_records.csv','sha256':sha256(raw).hexdigest()},review_progress(frame),evidence_completeness(frame))
    with Path(sys.argv[1]).open('xb') as output:output.write(bundle)
    print(json.dumps(verify_bundle(bundle),indent=2))
