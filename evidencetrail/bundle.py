"""Verify a bounded EvidenceTrail package without extracting files or judging evidence."""

from hashlib import sha256
from io import BytesIO
import json
import zlib
from zipfile import BadZipFile, ZipFile

PAYLOAD_NAMES = frozenset({"audit-summary.md", "findings.csv", "source-manifest.json",
                           "review-progress.json", "field-completeness.csv"})
MANIFEST_NAME = "artifact-manifest.json"
MAX_BUNDLE_BYTES = 64 * 1024 * 1024
MAX_EXPANDED_BYTES = 128 * 1024 * 1024


def payload_manifest(payloads: dict[str, bytes]) -> dict:
    if set(payloads) != PAYLOAD_NAMES or not all(isinstance(v, bytes) for v in payloads.values()):
        raise ValueError("Expected the five EvidenceTrail byte payloads.")
    return {"schema": "evidencetrail-artifacts/1", "algorithm": "sha256",
            "files": [{"path": name, "bytes": len(payloads[name]),
                       "sha256": sha256(payloads[name]).hexdigest()} for name in sorted(payloads)],
            "meaning": "Byte consistency only; not source authenticity or scientific verification."}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key in artifact manifest.")
        result[key] = value
    return result


def verify_bundle(content: bytes, expected_sha256: str | None = None) -> dict:
    """Return byte-consistency findings; reject invalid/oversized packaging.

    The manifest is unsigned. A person can change a payload and its manifest
    together, so a match is not proof of origin, history, or scientific truth.
    Legacy five-file bundles require regeneration, not a fabricated pass.
    """
    if not isinstance(content, bytes) or len(content) > MAX_BUNDLE_BYTES:
        raise ValueError("Expected ZIP bytes no larger than 64 MiB.")
    if expected_sha256 is not None:
        if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in expected_sha256):
            raise ValueError("Expected ZIP SHA-256 must contain exactly 64 hexadecimal characters.")
        expected_sha256 = expected_sha256.lower()
    try:
        with ZipFile(BytesIO(content)) as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate ZIP member names are ambiguous.")
            if MANIFEST_NAME not in names:
                raise ValueError("No artifact manifest; regenerate this legacy or unsupported bundle.")
            if set(names) != PAYLOAD_NAMES | {MANIFEST_NAME}:
                raise ValueError("Bundle must contain exactly the manifest and five declared payloads.")
            if any(item.is_dir() or item.flag_bits & 1 for item in infos):
                raise ValueError("Directories and encrypted members are unsupported.")
            if sum(item.file_size for item in infos) > MAX_EXPANDED_BYTES:
                raise ValueError("Expanded bundle exceeds 128 MiB.")
            if archive.getinfo(MANIFEST_NAME).file_size > 65536:
                raise ValueError("Artifact manifest exceeds 64 KiB.")
            manifest = json.loads(archive.read(MANIFEST_NAME), object_pairs_hook=_unique_object)
            if not isinstance(manifest, dict) or manifest.get("schema") != "evidencetrail-artifacts/1" or manifest.get("algorithm") != "sha256":
                raise ValueError("Unsupported artifact manifest schema or algorithm.")
            entries = manifest.get("files")
            if not isinstance(entries, list) or len(entries) != len(PAYLOAD_NAMES):
                raise ValueError("Manifest must list five payloads.")
            declared = {}
            for item in entries:
                if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
                    raise ValueError("Invalid artifact entry fields.")
                name, size, digest = item["path"], item["bytes"], item["sha256"]
                if not isinstance(name, str) or name not in PAYLOAD_NAMES or name in declared:
                    raise ValueError("Unknown or repeated artifact path.")
                if type(size) is not int or size < 0 or size > MAX_EXPANDED_BYTES:
                    raise ValueError("Invalid artifact byte count.")
                if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                    raise ValueError("Invalid SHA-256 digest.")
                declared[name] = item
            findings = []
            for name in sorted(PAYLOAD_NAMES):
                data = archive.read(name)
                if len(data) != declared[name]["bytes"]:
                    findings.append({"path": name, "code": "BYTE_COUNT_MISMATCH"})
                if sha256(data).hexdigest() != declared[name]["sha256"]:
                    findings.append({"path": name, "code": "SHA256_MISMATCH"})
    except (BadZipFile, UnicodeError, json.JSONDecodeError, RuntimeError, OSError, EOFError, NotImplementedError, zlib.error) as error:
        raise ValueError("Bundle could not be read as a supported EvidenceTrail ZIP.") from error
    report = {"schema": "evidencetrail-verification/1", "bundle_sha256": sha256(content).hexdigest(),
            "consistent": not findings, "checked_payloads": len(PAYLOAD_NAMES), "findings": findings,
            "scope": "Unsigned manifest consistency; no source, extraction, or scientific verification."}
    if expected_sha256 is not None:
        report["external_reference"] = {
            "expected_bundle_sha256": expected_sha256,
            "matches": report["bundle_sha256"] == expected_sha256,
            "scope": "Comparison with a caller-supplied reference; its trust and origin are not established by this tool.",
        }
    return report
