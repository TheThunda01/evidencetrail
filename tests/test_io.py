"""Literal input, workbook selection, and resource-limit regression tests."""

from io import BytesIO
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl import Workbook

from evidencetrail.audit import REQUIRED_COLUMNS, audit_table
from evidencetrail.io import MAX_UPLOAD_BYTES, list_sheets, load_table


HEADER = ",".join(REQUIRED_COLUMNS)


def workbook_bytes(configure=None):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Extraction"
    sheet.append(list(REQUIRED_COLUMNS))
    sheet.append(["R-1", "P-1", "setting", "NA", "Reported", "Page 1", "Pending"])
    if configure:
        configure(workbook)
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


class InputTests(unittest.TestCase):
    def test_csv_bom_literal_values_leading_zeros_and_quoted_multiline(self):
        content = (HEADER + '\n001,P-1,setting,NA,Reported,Page 1,Pending\n'
                   '002,P-1,setting,null,Reported,Page 2,Verified\n'
                   '003,P-2,setting,"line one\nline two",Reported,Page 3,Pending\n').encode("utf-8-sig")
        frame = load_table("input.CSV", content)
        self.assertEqual(frame["record_id"].tolist(), ["001", "002", "003"])
        self.assertEqual(frame["value"].tolist(), ["NA", "null", "line one\nline two"])
        self.assertFalse(audit_table(frame).findings)

    def test_duplicate_headers_rejected_before_renaming(self):
        for content in [b"record_id,record_id\n1,2\n", b"record_id, record_id \n1,2\n"]:
            with self.assertRaisesRegex(ValueError, "Duplicate column headers"):
                load_table("data.csv", content)
        content = workbook_bytes(lambda wb: setattr(wb.active["B1"], "value", " record_id "))
        with self.assertRaisesRegex(ValueError, "Duplicate column headers"):
            load_table("data.xlsx", content)

    def test_xlsx_sheet_selection_and_literal_strings(self):
        def configure(workbook):
            sheet = workbook.create_sheet("Other")
            sheet.append(list(REQUIRED_COLUMNS))
            sheet.append(["002", "P-2", "setting", "null", "Reported", "Page 2", "Verified"])
        content = workbook_bytes(configure)
        self.assertEqual(list_sheets(content), ["Extraction", "Other"])
        self.assertEqual(load_table("data.xlsx", content).iloc[0]["value"], "NA")
        frame = load_table("data.xlsx", content, "Other")
        self.assertEqual(frame.iloc[0]["record_id"], "002")
        self.assertEqual(frame.iloc[0]["value"], "null")
        self.assertFalse(audit_table(frame).findings)
        with self.assertRaisesRegex(ValueError, "selected worksheet"):
            load_table("data.xlsx", content, "Missing")

    def test_formulas_in_selected_xlsx_are_rejected_and_csv_stays_literal(self):
        content = workbook_bytes(lambda wb: setattr(wb.active["D2"], "value", "=1+1"))
        with self.assertRaisesRegex(ValueError, "formula at D2"):
            load_table("data.xlsx", content)
        csv = (HEADER + "\nR-1,P-1,setting,=1+1,Reported,Page 1,Pending\n").encode()
        self.assertEqual(load_table("data.csv", csv).iloc[0]["value"], "=1+1")

    def test_malformed_and_unsupported_inputs_have_friendly_errors(self):
        cases = [
            ("empty.csv", b"", "empty"),
            ("bad.csv", b"a,b\n1,2,3", "3 fields"),
            ("bad.csv", b'a,b\n"unclosed', "quoting"),
            ("bad.csv", b"a,b\n\xff,c", "UTF-8"),
            ("bad.csv", b"a,b\n\x00,c", "null bytes"),
            ("bad.xlsx", b"not a workbook", "XLSX"),
            ("data.xls", b"something", ".csv or .xlsx"),
        ]
        for filename, content, message in cases:
            with self.subTest(filename=filename, content=content):
                with self.assertRaisesRegex(ValueError, message):
                    load_table(filename, content)

    def test_malformed_workbook_xml_has_a_friendly_error(self):
        source = workbook_bytes()
        for damaged_file in ("xl/workbook.xml", "xl/worksheets/sheet1.xml"):
            output = BytesIO()
            with ZipFile(BytesIO(source)) as original, ZipFile(output, "w", ZIP_DEFLATED) as damaged:
                for name in original.namelist():
                    damaged.writestr(name, b"<broken" if name == damaged_file else original.read(name))
            with self.subTest(damaged_file=damaged_file):
                with self.assertRaisesRegex(ValueError, "could not be read"):
                    load_table("bad.xlsx", output.getvalue())

    def test_input_limits_apply_before_full_parsing(self):
        with self.assertRaisesRegex(ValueError, "5 MiB"):
            load_table("large.csv", b"x" * (MAX_UPLOAD_BYTES + 1))
        oversized_zip = BytesIO()
        with ZipFile(oversized_zip, "w", ZIP_DEFLATED) as archive:
            archive.writestr("large.xml", b"x" * (25 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, "25 MiB"):
            list_sheets(oversized_zip.getvalue())
        with self.assertRaisesRegex(ValueError, "10,000"):
            load_table("rows.csv", ("a\n" + "x\n" * 10_001).encode())
        with self.assertRaisesRegex(ValueError, "50"):
            load_table("columns.csv", ",".join(str(i) for i in range(51)).encode())
        content = workbook_bytes(lambda wb: setattr(wb.active["A10002"], "value", "extra"))
        with self.assertRaisesRegex(ValueError, "10,000"):
            load_table("rows.xlsx", content)

    def test_blank_csv_records_are_preserved_for_row_locations(self):
        frame = load_table("data.csv", (HEADER + "\n\nR-1,P-1,setting,NA,Reported,Page 1,Pending\n").encode())
        self.assertEqual(len(frame), 2)
        result = audit_table(frame)
        self.assertTrue(all(finding.row_numbers == (2,) for finding in result.findings))


if __name__ == "__main__":
    unittest.main()
