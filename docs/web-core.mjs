/** Deterministic extraction checks for the browser. No network or storage access. */

export const REQUIRED_COLUMNS = Object.freeze([
  "record_id", "report_id", "field", "value", "evidence_status", "source_locator", "review_status",
]);
export const EVIDENCE_STATUSES = Object.freeze([
  "Reported", "Not reported", "Unclear", "Explicitly absent", "Not applicable",
]);
export const REVIEW_STATUSES = Object.freeze(["Pending", "Verified", "Disagreement"]);
const MAX_ROWS = 10000;
const MAX_COLUMNS = 50;
const MAX_BYTES = 5 * 1024 * 1024;
const RULES = [
  "MISSING_RECORD_ID", "DUPLICATE_RECORD_ID", "MISSING_REPORT_ID", "MISSING_FIELD",
  "INVALID_EVIDENCE_STATUS", "INVALID_REVIEW_STATUS", "MISSING_REPORTED_VALUE",
  "MISSING_SOURCE_LOCATOR", "REVIEWER_DISAGREEMENT",
];
// Match Python str.strip(), including its control separators, without stripping
// a literal BOM from cell values. Only the file's initial BOM is removed.
const EDGE_WHITESPACE = /^[\x09-\x0d\x1c-\x20\x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\x09-\x0d\x1c-\x20\x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$/g;
const trim = (value) => value.replace(EDGE_WHITESPACE, "");
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);

function cellText(value) {
  if (value === null || value === undefined || (typeof value === "number" && Number.isNaN(value))) return "";
  if (typeof value === "boolean") return value ? "True" : "False";
  return trim(String(value));
}

function normalizedHeaders(headers) {
  if (!Array.isArray(headers)) throw new Error("Provide a table with a header array.");
  if (headers.length > MAX_COLUMNS) throw new Error("The table has too many columns. The limit is 50.");
  const names = headers.map(cellText);
  const seen = new Set();
  const duplicates = [];
  for (const name of names) {
    if (seen.has(name) && !duplicates.includes(name)) duplicates.push(name);
    seen.add(name);
  }
  if (duplicates.length) throw new Error(`Duplicate column headers: ${duplicates.map((name) => JSON.stringify(name)).join(", ")}. Give each column a unique name.`);
  return names;
}

function validatedTable(table, required = []) {
  if (!table || typeof table !== "object" || !Array.isArray(table.rows)) {
    throw new Error("Provide a table with headers and rows.");
  }
  if (table.rows.length > MAX_ROWS) throw new Error("The table has too many records. The limit is 10,000.");
  const headers = normalizedHeaders(table.headers);
  const missing = required.filter((column) => !headers.includes(column));
  if (missing.length) throw new Error(`Missing required columns: ${missing.join(", ")}.`);
  const rows = table.rows.map((row) => {
    if (!row || typeof row !== "object" || Array.isArray(row)) throw new Error("Each table row must be an object keyed by its column names.");
    return Object.fromEntries(headers.map((header, index) => [header, own(row, table.headers[index]) ? row[table.headers[index]] : ""]));
  });
  return { headers, rows };
}

/** Parse comma-separated UTF-8 text, keeping literal cell strings and blank rows. */
export function parseCSV(text) {
  if (typeof text !== "string") throw new Error("Provide CSV contents as text.");
  if (!text.length) throw new Error("The file is empty. Add a header row and try again.");
  if (new TextEncoder().encode(text).byteLength > MAX_BYTES) throw new Error("The file is too large. The upload limit is 5 MiB.");
  if (text.includes("\0")) throw new Error("The CSV contains null bytes and cannot be read as a text table.");
  if (text.startsWith("\uFEFF")) text = text.slice(1);
  let headers = null;
  const rows = [];
  let row = [], field = "", quoted = false, closedQuote = false, started = false;
  const malformed = () => new Error("The CSV could not be read. Check its quoting, separators, and cell lengths.");
  function finishRow() {
    if (headers === null) {
      if (!row.length) throw new Error("The table has no header row.");
      headers = normalizedHeaders(row);
    } else {
      if (!row.length) row = Array(headers.length).fill("");
      if (row.length !== headers.length) throw new Error(`CSV record ${rows.length + 2} has ${row.length} fields; the header has ${headers.length}.`);
      if (rows.length >= MAX_ROWS) throw new Error("The table has too many records. The limit is 10,000.");
      rows.push(Object.fromEntries(headers.map((header, index) => [header, row[index]])));
    }
    row = []; field = ""; closedQuote = false; started = false;
  }
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quoted) {
      if (char === '"') {
        if (text[index + 1] === '"') { field += '"'; index += 1; }
        else { quoted = false; closedQuote = true; }
      } else field += char;
      continue;
    }
    if (char === ",") {
      row.push(field); field = ""; started = true; closedQuote = false;
      if (row.length >= MAX_COLUMNS) throw new Error("The table has too many columns. The limit is 50.");
    } else if (char === "\r" || char === "\n") {
      if (started || row.length || closedQuote) row.push(field);
      finishRow();
      if (char === "\r" && text[index + 1] === "\n") index += 1;
    } else if (closedQuote) throw malformed();
    else if (char === '"' && field.length === 0) { quoted = true; started = true; }
    else { field += char; started = true; }
  }
  if (quoted) throw malformed();
  if (started || row.length || closedQuote) { row.push(field); finishRow(); }
  if (headers === null) throw new Error("The table has no header row.");
  return { headers, rows };
}

/** Suggest identity mappings only; no synonyms or semantic labels are guessed. */
export function identityMapping(headers) {
  const names = normalizedHeaders(headers);
  return Object.fromEntries(REQUIRED_COLUMNS.map((column) => [column, names.includes(column) ? column : null]));
}

/** Rename an explicit working copy; values and source row/column order stay intact. */
export function applyMapping(table, mapping) {
  const checked = validatedTable(table);
  if (!mapping || typeof mapping !== "object" || Array.isArray(mapping)) throw new Error("Provide a column mapping with one source column for each required field.");
  const unknown = Object.keys(mapping).filter((key) => !REQUIRED_COLUMNS.includes(key));
  if (unknown.length) throw new Error(`Unknown required-field names in the mapping: ${unknown.join(", ")}.`);
  const missing = REQUIRED_COLUMNS.filter((key) => !own(mapping, key) || typeof mapping[key] !== "string" || !trim(mapping[key]));
  if (missing.length) throw new Error(`Choose a source column for each required field: ${missing.join(", ")}.`);
  const chosen = REQUIRED_COLUMNS.map((key) => [key, trim(mapping[key])]);
  const nonexistent = chosen.map(([, value]) => value).filter((value) => !checked.headers.includes(value));
  if (nonexistent.length) throw new Error(`Mapped source columns were not found: ${nonexistent.join(", ")}.`);
  if (new Set(chosen.map(([, value]) => value)).size !== chosen.length) throw new Error("Each source column can be mapped only once. Choose a different column for each required field.");
  const renamed = new Map(chosen.map(([canonical, source]) => [source, canonical]));
  const headers = checked.headers.map((header) => renamed.get(header) ?? header);
  const collisions = [...new Set(headers.filter((header, index) => headers.indexOf(header) !== index))].sort();
  if (collisions.length) throw new Error(`Mapped names conflict with columns retained from the input: ${collisions.join(", ")}. Map those existing columns instead, or rename conflicting columns in a separate copy.`);
  return {
    headers,
    rows: checked.rows.map((row) => Object.fromEntries(headers.map((header, index) => [header, row[checked.headers[index]]]))),
  };
}

/** Audit structure and recorded metadata. A clean audit does not verify evidence. */
export function audit(table) {
  const checked = validatedTable(table, REQUIRED_COLUMNS);
  const findings = [];
  const byId = new Map();
  const reportIds = new Set();
  const review_counts = { records: checked.rows.length, pending: 0, verified: 0, disagreement: 0, invalid: 0 };
  const reviewFields = new Map([["Pending", "pending"], ["Verified", "verified"], ["Disagreement", "disagreement"]]);
  const fieldGroups = new Map();
  const statusFields = new Map([
    ["Reported", "reported"], ["Not reported", "not_reported"], ["Unclear", "unclear"],
    ["Explicitly absent", "explicitly_absent"], ["Not applicable", "not_applicable"],
  ]);
  checked.rows.forEach((original, index) => {
    const row = Object.fromEntries(REQUIRED_COLUMNS.map((column) => [column, cellText(original[column])]));
    const number = index + 2;
    const add = (code, severity, message, suggestion) => findings.push({ code, severity, row_numbers: [number], record_id: row.record_id, field: row.field, message, suggestion });
    if (row.report_id) reportIds.add(row.report_id);
    if (row.record_id) {
      if (!byId.has(row.record_id)) byId.set(row.record_id, []);
      byId.get(row.record_id).push({ number, field: row.field });
    }
    if (!row.record_id) add("MISSING_RECORD_ID", "error", "The record ID is empty.", "Assign a unique ID to this extraction record.");
    if (!row.report_id) add("MISSING_REPORT_ID", "error", "The report ID is empty.", "Add the ID of the source report for this record.");
    if (!row.field) add("MISSING_FIELD", "error", "The extraction field is empty.", "Name the question or field this record addresses.");
    if (!EVIDENCE_STATUSES.includes(row.evidence_status)) add("INVALID_EVIDENCE_STATUS", "error", "The evidence status is missing or unrecognized.", `Use one of: ${EVIDENCE_STATUSES.join(", ")}.`);
    if (!REVIEW_STATUSES.includes(row.review_status)) add("INVALID_REVIEW_STATUS", "error", "The review status is missing or unrecognized.", `Use one of: ${REVIEW_STATUSES.join(", ")}.`);
    if (row.evidence_status === "Reported" && !row.value) add("MISSING_REPORTED_VALUE", "review", "The evidence status is Reported, but the value is empty.", "Check the source and add the value, or correct the evidence status.");
    if (["Reported", "Explicitly absent"].includes(row.evidence_status) && !row.source_locator) add("MISSING_SOURCE_LOCATOR", "review", "This evidence status needs a source locator, but none is recorded.", "Add a page, section, table, figure, or another precise location in the source.");
    if (row.review_status === "Disagreement") add("REVIEWER_DISAGREEMENT", "review", "The record is marked as a reviewer disagreement.", "Resolve the disagreement through the project's review process and document the decision.");
    const reviewKey = reviewFields.get(row.review_status);
    review_counts[reviewKey || "invalid"] += 1;
    if (!fieldGroups.has(row.field)) fieldGroups.set(row.field, {
      field: row.field, records: 0, reported: 0, not_reported: 0, unclear: 0, explicitly_absent: 0,
      not_applicable: 0, invalid_evidence_status: 0, missing_reported_value: 0, missing_source_locator: 0,
    });
    const group = fieldGroups.get(row.field);
    group.records += 1;
    group[statusFields.get(row.evidence_status) || "invalid_evidence_status"] += 1;
    group.missing_reported_value += Number(row.evidence_status === "Reported" && !row.value);
    group.missing_source_locator += Number(["Reported", "Explicitly absent"].includes(row.evidence_status) && !row.source_locator);
  });
  for (const [record_id, occurrences] of byId) {
    if (occurrences.length <= 1) continue;
    findings.push({ code: "DUPLICATE_RECORD_ID", severity: "error", row_numbers: occurrences.map((entry) => entry.number), record_id,
      field: new Set(occurrences.map((entry) => entry.field)).size === 1 ? occurrences[0].field : "",
      message: "The same record ID is used by more than one row.",
      suggestion: "Check whether these are duplicate records or distinct extractions that need unique IDs.",
    });
  }
  findings.sort((first, second) => first.row_numbers[0] - second.row_numbers[0] || RULES.indexOf(first.code) - RULES.indexOf(second.code));
  return { findings, records_count: checked.rows.length, report_count: reportIds.size, review_counts, field_summary: [...fieldGroups.values()] };
}

/** Match only complete unique (report_id, field) keys; never infer adjudication. */
export function compare(left, right) {
  const required = ["report_id", "field", "record_id", "value", "evidence_status", "source_locator"];
  const tables = { left: validatedTable(left, required), right: validatedTable(right, required) };
  const sides = {}, groups = {}, blocked = { left: new Set(), right: new Set() };
  const issues = [];
  for (const side of ["left", "right"]) {
    groups[side] = new Map();
    sides[side] = tables[side].rows.map((original, index) => {
      const row = Object.fromEntries(required.map((column) => [column, cellText(original[column])]));
      row.number = index + 2;
      row.key = JSON.stringify([row.report_id, row.field]);
      if (!row.report_id || !row.field) {
        blocked[side].add(row.number);
        issues.push({ side, row_numbers: String(row.number), reason: "Missing key", key: row.key });
      } else {
        if (!groups[side].has(row.key)) groups[side].set(row.key, []);
        groups[side].get(row.key).push(row);
      }
      return row;
    });
  }
  const duplicateKeys = new Set();
  for (const byKey of Object.values(groups)) for (const [key, rows] of byKey) if (rows.length > 1) duplicateKeys.add(key);
  for (const side of ["left", "right"]) {
    for (const [key, rows] of groups[side]) {
      if (!duplicateKeys.has(key)) continue;
      for (const row of rows) blocked[side].add(row.number);
      issues.push({ side, row_numbers: rows.map((row) => row.number).join(", "), reason: rows.length > 1 ? "Duplicate key" : "Counterpart has duplicate key", key });
    }
  }
  const available = Object.fromEntries(["left", "right"].map((side) => [side, new Map(sides[side].filter((row) => !blocked[side].has(row.number)).map((row) => [row.key, row]))]));
  const pairs = [];
  function addPair(first, second) {
    const source = first || second;
    const pair = { report_id: source.report_id, field: source.field, left_row: first?.number ?? null, right_row: second?.number ?? null };
    for (const column of ["record_id", "value", "evidence_status", "source_locator"]) {
      pair[`left_${column}`] = first?.[column] ?? "";
      pair[`right_${column}`] = second?.[column] ?? "";
    }
    const differences = first && second ? ["value", "evidence_status"].filter((column) => first[column] !== second[column]) : [];
    pair.status = first && second ? (differences.length ? "Difference" : "Agreement") : (first ? "Left only" : "Right only");
    pair.different_fields = differences.join(", ");
    pair.locator_diff = Boolean(first && second && first.source_locator !== second.source_locator);
    pairs.push(pair);
  }
  for (const [key, row] of available.left) addPair(row, available.right.get(key));
  for (const [key, row] of available.right) if (!available.left.has(key)) addPair(null, row);
  const count = (status) => pairs.filter((pair) => pair.status === status).length;
  const summary = { comparable_pairs: count("Agreement") + count("Difference"), agreements: count("Agreement"), differences: count("Difference"), left_only: count("Left only"), right_only: count("Right only"), blocked_rows: blocked.left.size + blocked.right.size };
  issues.sort((first, second) => (first.side === second.side ? 0 : first.side === "left" ? -1 : 1) || parseInt(first.row_numbers, 10) - parseInt(second.row_numbers, 10));
  return { pairs, issues, summary };
}

/** Export a spreadsheet-safe UTF-8 CSV string, with BOM and CRLF line endings. */
export function csvExport(rows, columns) {
  if (!Array.isArray(rows)) throw new Error("Provide an array of export rows.");
  if (columns === undefined) columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  if (!Array.isArray(columns)) throw new Error("Provide export column names as an array.");
  function escaped(value) {
    let text = value === null || value === undefined ? "" : typeof value === "boolean" ? (value ? "True" : "False") : String(value);
    if (typeof value === "string" && /^[ \t\r\n\v\f\uFEFF]*[=+\-@]/.test(text)) text = "'" + text;
    if (/[",\r\n]/.test(text)) text = '"' + text.replaceAll('"', '""') + '"';
    return text;
  }
  const lines = [columns.map((column) => escaped(String(column))).join(",")];
  for (const row of rows) lines.push(columns.map((column) => escaped(own(row, column) ? row[column] : "")).join(","));
  return "\uFEFF" + lines.join("\r\n") + "\r\n";
}
