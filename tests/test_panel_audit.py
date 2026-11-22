"""Synthetic offline fixtures for read-only inventory and private output rules."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import audit_panel_workbook as audit


@unittest.skipUnless(importlib.util.find_spec('openpyxl'), 'Optional requirements-panel.txt needed')
class PanelAuditTests(unittest.TestCase):
    def test_formulas_errors_hidden_sheets_and_original_bytes(self):
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.xlsx'
            book = Workbook()
            sheet = book.active
            sheet.append(['Country', 'Value', 'Value', None])
            sheet.append(['Example', 0, '=B2+1', '#DIV/0!'])
            sheet.append(['Second', None, 4, None])
            book.create_sheet('Notes').sheet_state = 'hidden'
            book.save(path)
            original = path.read_bytes()
            result = audit.inspect_workbook(path)
            self.assertEqual(original, path.read_bytes())
            self.assertTrue(result['input_bytes_unchanged'])
            self.assertFalse(result['definitions_confirmed'])
            entry = result['sheets'][0]
            self.assertEqual(entry['duplicate_headers'], ['Value'])
            self.assertEqual(entry['blank_header_columns'], [4])
            self.assertEqual(entry['formula_cells'], ['C2'])
            self.assertEqual(entry['error_cells'], ['D2'])
            self.assertEqual(entry['blank_cells_by_column']['2'], 1)
            self.assertEqual(result['sheets'][1]['state'], 'hidden')

    def test_route_sample_is_not_accepted_as_panel(self):
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.xlsx'
            book = Workbook(); sheet = book.active
            sheet.append(['Year', 'Month', 'OriginAirportCode', 'DestinationAirportCode',
                          'OriginCountryCode', 'DestinationCountryCode', 'PrimaryAirlineCode',
                          'DepartingSeats', 'Departures'])
            row = [2017, 1, 'AAA', 'BBB', 'ZA', 'ZA', 'XX', 100, 1]
            sheet.append(row); sheet.append(row)
            book.save(path)
            entry = audit.inspect_workbook(path)['sheets'][0]
            self.assertEqual(entry['classification'], 'MONTHLY_ROUTE_SAMPLE_NOT_QUARTERLY_PANEL')
            self.assertEqual(entry['duplicate_route_keys'], 1)
            self.assertEqual(entry['us_endpoint_rows'], 0)

    def test_invalid_input_is_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            audit.inspect_workbook('original.csv')
        with self.assertRaises(ValueError):
            audit.inspect_workbook('original.xlsx', 0)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'broken.xlsx'; path.write_text('not an Excel file')
            with self.assertRaises(Exception):
                audit.inspect_workbook(path)

    def test_outputs_private_and_no_overwrite(self):
        root = Path(audit.__file__).resolve().parent
        with self.assertRaises(ValueError):
            audit.write_audit({}, root / 'public-audit.json')
        (root / 'runs').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root / 'runs') as folder:
            output = Path(folder) / 'audit.json'
            audit.write_audit({'test': True}, output)
            first = output.read_bytes()
            with self.assertRaises(FileExistsError):
                audit.write_audit({'replacement': True}, output)
            self.assertEqual(output.read_bytes(), first)
