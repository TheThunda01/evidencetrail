import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  REQUIRED_COLUMNS, EVIDENCE_STATUSES, REVIEW_STATUSES,
  parseCSV, identityMapping, applyMapping, audit, compare, csvExport,
} from "../docs/web-core.mjs";

const fixtures = JSON.parse(readFileSync(new URL("../docs/web-parity.json", import.meta.url), "utf8"));
const table = (rows, headers = REQUIRED_COLUMNS) => ({ headers: [...headers], rows });
const record = (changes = {}) => ({
  record_id: "R1", report_id: "P1", field: "setting", value: "National",
  evidence_status: "Reported", source_locator: "Page 1", review_status: "Pending", ...changes,
});

for (const item of fixtures.audit_cases) {
  test(`Python audit parity: ${item.name}`, () => {
    const actual = audit(item.table);
    actual.findings = actual.findings.map(({ code, severity, row_numbers, record_id, field }) => ({ code, severity, row_numbers, record_id, field }));
    assert.deepEqual(actual, item.expected);
  });
}
for (const item of fixtures.mapping_cases) {
  test(`Python mapping parity: ${item.name}`, () => {
    assert.deepEqual(applyMapping(item.table, item.mapping), item.expected);
  });
}
for (const item of fixtures.comparison_cases) {
  test(`Python comparison parity: ${item.name}`, () => {
    assert.deepEqual(compare(item.left, item.right), item.expected);
  });
}

test("CSV accepts BOM, CRLF, quoted commas, doubled quotes and embedded newlines", () => {
  const parsed = parseCSV('\uFEFF id ,value\r\n001,"NA, null"\r\n002,"line one\r\nline ""two"""\r\n');
  assert.deepEqual(parsed, {
    headers: ["id", "value"], rows: [
      { id: "001", value: "NA, null" },
      { id: "002", value: 'line one\r\nline "two"' },
    ],
  });
  assert.equal(parseCSV("id,value\n1,NA\n2,null").rows[0].value, "NA");
  assert.deepEqual(parseCSV("a,b\n\n1,2\n").rows, [{ a: "", b: "" }, { a: "1", b: "2" }]);
  assert.equal(parseCSV("a,b\r1,2\r").rows.length, 1);
});

test("CSV malformed records and duplicate normalized headers are rejected", () => {
  for (const input of ["a,a\n1,2", "a, a \n1,2"]) assert.throws(() => parseCSV(input), /Duplicate column headers/);
  assert.throws(() => parseCSV('a,b\n1,"unclosed'), /quoting/);
  assert.throws(() => parseCSV('a,b\n1,"closed" extra'), /quoting/);
  assert.throws(() => parseCSV("a,b\n1,2,3"), /3 fields/);
  assert.throws(() => parseCSV("a,b\n1"), /1 fields/);
  assert.throws(() => parseCSV(""), /empty/);
  assert.throws(() => parseCSV("\uFEFF"), /no header row/);
  assert.throws(() => parseCSV("a\n\0"), /null bytes/);
  assert.throws(() => parseCSV("\na,b"), /no header row/);
});

test("CSV resource limits include UTF-8 byte length and exact row/column boundaries", () => {
  assert.throws(() => parseCSV("a\n" + "x".repeat(5 * 1024 * 1024)), /5 MiB/);
  assert.throws(() => parseCSV("a\n" + "é".repeat(3 * 1024 * 1024)), /5 MiB/);
  assert.throws(() => parseCSV("a\n" + "x\n".repeat(10001)), /10,000/);
  assert.equal(parseCSV("a\n" + "x\n".repeat(10000)).rows.length, 10000);
  assert.throws(() => parseCSV(Array.from({ length: 51 }, (_, i) => `c${i}`).join(",")), /50/);
  assert.equal(parseCSV(Array.from({ length: 50 }, (_, i) => `c${i}`).join(",")).headers.length, 50);
});

test("Mapping is explicit, preserves extra columns and original cell values", () => {
  const headers = ["ID", "Report", "Question", "Answer", "Evidence", "Location", "Review", "notes"];
  const original = table([Object.fromEntries(headers.map((key, i) => [key, [`001`, `P1`, `setting`, ` NA `, `Reported`, `p1`, ` Pending `, `Keep`][i]]))], headers);
  const before = structuredClone(original);
  const mapping = Object.fromEntries(REQUIRED_COLUMNS.map((key, i) => [key, headers[i]]));
  const result = applyMapping(original, mapping);
  assert.deepEqual(original, before);
  assert.deepEqual(result.headers, [...REQUIRED_COLUMNS, "notes"]);
  assert.equal(result.rows[0].value, " NA ");
  assert.equal(result.rows[0].notes, "Keep");
  result.rows[0].value = "changed";
  assert.deepEqual(original, before);
  assert.equal(identityMapping([" record_id ", "Report ID"]).record_id, "record_id");
  assert.equal(identityMapping([" record_id ", "Report ID"]).report_id, null);
});

test("Mapping rejects incomplete, reused, unknown and retained-column collisions", () => {
  const original = table([record()], [...REQUIRED_COLUMNS, "new_id"]);
  const identity = identityMapping(original.headers);
  assert.throws(() => applyMapping(original, { ...identity, value: null }), /each required field/);
  assert.throws(() => applyMapping(original, { ...identity, value: "missing" }), /were not found/);
  assert.throws(() => applyMapping(original, { ...identity, value: "field" }), /only once/);
  assert.throws(() => applyMapping(original, { ...identity, bogus: "value" }), /Unknown required-field/);
  assert.throws(() => applyMapping(original, { ...identity, record_id: "new_id" }), /conflict with columns retained/);
  assert.throws(() => audit(table([], ["field", " field "])), /Duplicate column/);
  assert.throws(() => applyMapping(table(Array(10001).fill(record())), identity), /10,000/);
});

test("Pending and unrecognized statuses stay distinct from audit findings", () => {
  const clean = audit(table([record()]));
  assert.equal(clean.findings.length, 0);
  assert.deepEqual(clean.review_counts, { records: 1, pending: 1, verified: 0, disagreement: 0, invalid: 0 });
  const unusual = audit(table([
    record({ review_status: "constructor" }),
    record({ record_id: "R2", review_status: "__proto__" }),
    record({ record_id: "R3", review_status: "toString" }),
  ]));
  assert.deepEqual(unusual.review_counts, { records: 3, pending: 0, verified: 0, disagreement: 0, invalid: 3 });
  assert.equal(unusual.findings.filter((item) => item.code === "INVALID_REVIEW_STATUS").length, 3);
});

test("BOM text, unicode whitespace and evidence-status distinctions match Python", () => {
  const output = audit(table([
    record({ record_id: "\x85R1\x1c", value: "NA", evidence_status: "\u2003Reported\u2003" }),
    record({ record_id: "R2", value: "", source_locator: "", evidence_status: "Not reported" }),
    record({ record_id: "R3", value: "", source_locator: "", evidence_status: "Unclear" }),
    record({ record_id: "R4", value: "", source_locator: "", evidence_status: "Not applicable" }),
    record({ record_id: "R5", value: "", source_locator: "", evidence_status: "Explicitly absent" }),
    record({ record_id: "R6", evidence_status: "\uFEFFReported" }),
  ]));
  assert.deepEqual(output.findings.map((item) => [item.code, item.row_numbers]), [
    ["MISSING_SOURCE_LOCATOR", [6]], ["INVALID_EVIDENCE_STATUS", [7]],
  ]);
  assert.equal(output.field_summary[0].invalid_evidence_status, 1);
  assert.equal(output.field_summary[0].not_reported, 1);
  assert.equal(output.field_summary[0].unclear, 1);
  assert.equal(output.field_summary[0].not_applicable, 1);
});

test("Special header names remain data and do not modify object prototypes", () => {
  const parsed = parseCSV("__proto__,constructor\ntext,value\n");
  assert.equal(Object.getPrototypeOf(parsed.rows[0]), Object.prototype);
  assert.equal(Object.hasOwn(parsed.rows[0], "__proto__"), true);
  assert.equal(parsed.rows[0].__proto__, "text");
  assert.equal({}.polluted, undefined);
  assert.equal(parseCSV(csvExport(parsed.rows, parsed.headers)).rows[0].__proto__, "text");
});

test("Comparison avoids cross joins, blocks counterparts and handles delimiter keys", () => {
  const left = table([record(), record({ record_id: "R2" }), record({ record_id: "R3", report_id: "a|b", field: "c" })]);
  const right = table([record({ record_id: "B1" }), record({ record_id: "B2", report_id: "a", field: "b|c" })]);
  const before = structuredClone([left, right]);
  const result = compare(left, right);
  assert.equal(result.summary.blocked_rows, 3);
  assert.equal(result.summary.comparable_pairs, 0);
  assert.equal(result.summary.left_only, 1);
  assert.equal(result.summary.right_only, 1);
  assert.equal(result.pairs.length, 2);
  assert.deepEqual([left, right], before);
});

test("Comparison handles locator-only differences without declaring value disagreement", () => {
  const result = compare(table([record()]), table([record({ record_id: "B1", value: " National ", source_locator: "Page 2" })]));
  assert.equal(result.pairs[0].status, "Agreement");
  assert.equal(result.pairs[0].locator_diff, true);
  assert.equal(result.pairs[0].different_fields, "");
  assert.equal(result.summary.agreements, 1);
});

test("CSV exports escape formulas, preserve typed numbers and quote multiline text", () => {
  const rows = [{ "=heading": "\t @SUM(1,2)", plain: 'line 1\n"line 2"', number: -3, missing: null }];
  const before = structuredClone(rows);
  const exported = csvExport(rows);
  assert.ok(exported.startsWith("\uFEFF"));
  assert.ok(exported.endsWith("\r\n"));
  const parsed = parseCSV(exported);
  assert.equal(parsed.headers[0], "'=heading");
  assert.equal(parsed.rows[0]["'=heading"], "'\t @SUM(1,2)");
  assert.equal(parsed.rows[0].plain, 'line 1\n"line 2"');
  assert.equal(parsed.rows[0].number, "-3");
  assert.equal(parsed.rows[0].missing, "");
  assert.deepEqual(rows, before);
  assert.equal(csvExport([], ["id", "value"]), "\uFEFFid,value\r\n");
});

test("Documented label arrays cannot be changed accidentally", () => {
  assert.equal(REQUIRED_COLUMNS.length, 7);
  assert.equal(EVIDENCE_STATUSES.length, 5);
  assert.equal(REVIEW_STATUSES.length, 3);
  assert.throws(() => REQUIRED_COLUMNS.push("extra"));
});
