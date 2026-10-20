from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
from zipfile import ZipFile, ZIP_DEFLATED
from evidencetrail.bundle import MANIFEST_NAME, PAYLOAD_NAMES, payload_manifest, verify_bundle


def make_bundle(payloads=None, manifest=None, extra=None):
    payloads = payloads or {name: (name + '\n').encode() for name in PAYLOAD_NAMES}
    output = BytesIO()
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as z:
        for name, value in payloads.items(): z.writestr(name, value)
        if manifest is not False: z.writestr(MANIFEST_NAME, json.dumps(manifest or payload_manifest(payloads)))
        if extra:
            for name, value in extra: z.writestr(name, value)
    return output.getvalue()


class VerificationTests(unittest.TestCase):
    def test_manifest_covers_exact_payload_bytes(self):
        report = verify_bundle(make_bundle())
        self.assertTrue(report['consistent']);self.assertEqual(report['checked_payloads'], 5)
        self.assertEqual(report['findings'], []);self.assertIn('Unsigned', report['scope'])

    def test_changed_payload_is_not_consistent(self):
        old = {n:n.encode() for n in PAYLOAD_NAMES};changed = {**old, 'findings.csv': b'changed\n'}
        result = verify_bundle(make_bundle(changed, payload_manifest(old)))
        self.assertFalse(result['consistent'])
        self.assertIn({'path':'findings.csv','code':'SHA256_MISMATCH'},result['findings'])

    def test_legacy_and_extra_members_fail_explicitly(self):
        for data in [make_bundle(manifest=False),make_bundle(extra=[('../unexpected',b'x')])]:
            with self.assertRaises(ValueError): verify_bundle(data)

    def test_duplicate_archive_member_fails(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');data=make_bundle(extra=[('findings.csv',b'other')])
        with self.assertRaisesRegex(ValueError,'Duplicate'): verify_bundle(data)

    def test_manifest_shape_and_digest_validation(self):
        original=payload_manifest({n:n.encode() for n in PAYLOAD_NAMES})
        variants=[{**original,'schema':'unknown'}, {**original,'files':[]}]
        for key,value in [('path','../x'),('bytes',True),('sha256','z'*64)]:
            m=json.loads(json.dumps(original));m['files'][0][key]=value;variants.append(m)
        for m in variants:
            with self.subTest(m=m),self.assertRaises(ValueError):verify_bundle(make_bundle(manifest=m))

    def test_manifest_replacement_is_not_authentication(self):
        payloads={n:b'new valid bytes' for n in PAYLOAD_NAMES}
        self.assertTrue(verify_bundle(make_bundle(payloads))['consistent'])

    def test_external_reference_is_optional_and_checks_entire_zip(self):
        raw=make_bundle()
        baseline=verify_bundle(raw)
        self.assertNotIn('external_reference',baseline)
        matched=verify_bundle(raw,sha256(raw).hexdigest().upper())
        self.assertTrue(matched['external_reference']['matches'])
        self.assertEqual({k:v for k,v in matched.items() if k!='external_reference'},baseline)
        changed=make_bundle({n:b'replaced with consistent payloads' for n in PAYLOAD_NAMES})
        result=verify_bundle(changed,sha256(raw).hexdigest())
        self.assertTrue(result['consistent'])
        self.assertFalse(result['external_reference']['matches'])

    def test_expected_digest_requires_exact_hexadecimal_value(self):
        for value in ['', 'a'*63, 'g'*64, 1, ' '+ 'a'*64]:
            with self.subTest(value=value),self.assertRaises(ValueError):verify_bundle(make_bundle(),value)

    def test_invalid_zip_and_duplicate_json_are_rejected(self):
        with self.assertRaises(ValueError):verify_bundle(b'not zip')
        out=BytesIO()
        with ZipFile(out,'w') as z:
            for n in PAYLOAD_NAMES:z.writestr(n,b'')
            z.writestr(MANIFEST_NAME,b'{"schema":"x","schema":"y"}')
        with self.assertRaisesRegex(ValueError,'Duplicate JSON'):verify_bundle(out.getvalue())

    def test_cli_exit_codes_and_bundle_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'audit.zip';raw=make_bundle();p.write_bytes(raw)
            run=lambda:subprocess.run([sys.executable,'-m','evidencetrail.verify_bundle',str(p)],capture_output=True,text=True)
            good=run();self.assertEqual(good.returncode,0,good.stderr)
            self.assertEqual(json.loads(good.stdout)['bundle_sha256'],sha256(raw).hexdigest())
            old={n:n.encode() for n in PAYLOAD_NAMES}
            p.write_bytes(make_bundle({**old,'findings.csv':b'x'},payload_manifest(old)));self.assertEqual(run().returncode,1)
            p.write_bytes(b'bad');self.assertEqual(run().returncode,2)

    def test_cli_expected_digest_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'audit.zip';raw=make_bundle();p.write_bytes(raw)
            def run(digest):
                return subprocess.run([sys.executable,'-m','evidencetrail.verify_bundle',str(p),'--expected-sha256',digest],capture_output=True,text=True)
            self.assertEqual(run(sha256(raw).hexdigest()).returncode,0)
            wrong=run('0'*64)
            self.assertEqual(wrong.returncode,1)
            self.assertTrue(json.loads(wrong.stdout)['consistent'])
            self.assertFalse(json.loads(wrong.stdout)['external_reference']['matches'])
            bad=run('bad');self.assertEqual(bad.returncode,2);self.assertEqual(bad.stdout,'')

if __name__=='__main__':unittest.main()
