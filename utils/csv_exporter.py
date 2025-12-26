import csv
from typing import List, Dict
from config.settings import CSV_ENCODING


class CSVExporter:
    def __init__(self, encoding: str = CSV_ENCODING):
        self.encoding = encoding

    def export_to_csv(self, data: List[Dict], filename: str, mode: str = 'w'):
        if not data:
            return
        keys = data[0].keys()
        with open(filename, mode, encoding=self.encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            if mode == 'w':
                writer.writeheader()
            for row in data:
                writer.writerow(row)

    def merge_csv_files(self, input_files: List[str], output_file: str):
        # Minimal merge implementation: read each and append; dedupe to be added
        combined = []
        for fpath in input_files:
            with open(fpath, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(f)
                for r in reader:
                    combined.append(r)
        self.export_to_csv(combined, output_file, mode='w')
