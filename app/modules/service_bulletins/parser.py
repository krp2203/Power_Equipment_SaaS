import re
import subprocess
import json
import logging
from datetime import datetime

class BulletinParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.text_output = ""
        self.lines = []

    def parse(self):
        try:
            # Extract text
            self.text_output = subprocess.check_output(['pdftotext', '-layout', self.file_path, '-'], text=True)
            self.lines = [l.strip() for l in self.text_output.split('\n') if l.strip()]
            
            data = {
                'sb_number': self._extract_sb_number(),
                'issue_date': self._extract_issue_date(),
                'title': self._extract_title(),
                'description': self._extract_description(),
                'warranty_code': self._extract_warranty_codes(),
                'labor_hours': self._extract_labor_hours(),
                'required_parts': self._extract_parts(),
                'models': self._extract_models_and_ranges()
            }
            return data
        except Exception as e:
            logging.error(f"Error parsing PDF {self.file_path}: {e}")
            raise e

    def _extract_sb_number(self):
        # Extract SB Number (e.g., "SERVICE BULLETIN 233" or "SB - 235")
        for line in self.lines[:5]:
            sb_match = re.search(r'SERVICE\s+BULLETIN\s+(\d+)', line, re.IGNORECASE)
            if not sb_match: sb_match = re.search(r'SB[\s-]+(\d+)', line, re.IGNORECASE)
            if not sb_match: sb_match = re.search(r'SB(\d+)', line, re.IGNORECASE)
            if sb_match: return sb_match.group(1)
        return None

    def _extract_issue_date(self):
        for line in self.lines[:20]:
            # Format 1: MM/DD/YYYY
            date_match = re.search(r'ISSUED?:\s*(\d{2}/\d{2}/\d{4})', line, re.IGNORECASE)
            if date_match:
                try:
                    return datetime.strptime(date_match.group(1), '%m/%d/%Y').date()
                except: pass
            
            # Format 2: Month DD, YYYY
            date_match = re.search(r'ISSUED?:\s*([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,\s*(\d{4})', line, re.IGNORECASE)
            if date_match:
                month, day, year = date_match.groups()
                # Fix known typos
                if 'urary' in month.lower(): month = 'February'
                try:
                    return datetime.strptime(f"{month} {day}, {year}", '%B %d, %Y').date()
                except: pass
        return None

    def _extract_title(self):
        # Extract Title (usually after "SUBJECT:" or "Mandatory")
        for i, line in enumerate(self.lines):
            if 'SUBJECT:' in line.upper():
                title = line.replace('SUBJECT:', '').strip()
                if not title and i + 1 < len(self.lines):
                    title = self.lines[i + 1].strip()
                return title
            elif 'MANDATORY' in line.upper():
                return line.strip()
        return None

    def _extract_description(self):
        description_lines = []
        in_situation = False
        for line in self.lines:
            if 'SITUATION:' in line.upper():
                in_situation = True
                desc = line.replace('SITUATION:', '').strip()
                if desc: description_lines.append(desc)
                continue
            if in_situation:
                if any(k in line.upper() for k in ['SOLUTION:', 'UNITS', 'REQUIRED:', 'WARRANTY:']):
                    break
                description_lines.append(line)
        return ' '.join(description_lines).strip()

    def _extract_warranty_codes(self):
        codes = []
        for line in self.lines:
            match = re.search(r'\b(X\d+-\d+)\b', line, re.IGNORECASE)
            if match:
                code = match.group(1).upper()
                if code not in codes: codes.append(code)
        return ', '.join(codes) if codes else None

    def _extract_labor_hours(self):
        hours = []
        for line in self.lines:
            match = re.search(r'(\d*\.?\d+)\s*(?:hrs?\.?|hours?)', line, re.IGNORECASE)
            if match and 'labor' in line.lower():
                h = match.group(1)
                if h not in hours: hours.append(h)
        return ', '.join(hours) if hours else None

    def _extract_parts(self):
        parts = []
        for line in self.lines:
            if 'REQUIRED:' in line.upper():
                parts_text = line.split('REQUIRED:', 1)[1].strip()
                matches = re.findall(r'\b(\d{5,})\b', parts_text)
                for part in matches:
                     parts.append(part)
        return json.dumps(parts) if parts else '[]'

    def _extract_models_and_ranges(self):
        model_ranges = []
        models_found = []
        raw_ranges = []
        in_section = False
        
        # Scan lines
        for line in self.lines:
            # Header Detection
            upper_line = line.upper()
            if not in_section:
                if 'UNITS' in upper_line and 'AFFECTED' in upper_line: 
                    in_section = True
                    logging.debug(f"Parser: Found 'AFFECTED UNITS' header: {line}")
                elif 'SERIAL' in upper_line and 'RANGE' in upper_line: 
                    in_section = True
                    logging.debug(f"Parser: Found 'SERIAL RANGE' header: {line}")
            
            if in_section:
                # 0. Combined Model + Serial on one line
                # e.g. "SVRII-36A-23BV   K7100001 - K7100345"
                # Improved model regex: starts with 2+ letters, contains alphanumeric and hyphens
                model_regex = r'([A-Z]{2,}[A-Z0-9-]*(?:II)?(?:-[A-Z0-9]+)*)'
                # Improved serial regex: matches 5+ alphanumeric characters
                serial_regex = r'([A-Z0-9]{5,})'
                
                combined_pattern = rf'{model_regex}\s+{serial_regex}\s*(?:-|to)\s*{serial_regex}'
                combined = re.search(combined_pattern, line, re.IGNORECASE)
                
                if combined:
                    model_ranges.append({
                        'model': combined.group(1).strip(),
                        'serial_start': combined.group(2).strip().upper(),
                        'serial_end': combined.group(3).strip().upper()
                    })
                    logging.debug(f"Parser: Matched combined line: {line} -> {model_ranges[-1]}")
                    continue

                # 1. Models (standalone line)
                # Matches something that looks like a model number but is on its own line
                if re.match(rf'^\s*{model_regex}\s*$', line, re.IGNORECASE):
                     m = line.strip().upper()
                     if m not in ['MODEL', 'SERIAL', 'RANGE', 'UNITS', 'AFFECTED', 'NUMBER']:
                         models_found.append(m)
                         logging.debug(f"Parser: Found potential standalone model: {m}")
                         continue

                # 2. Ranges (standalone line)
                rng = re.search(rf'\b{serial_regex}\b\s*(?:-|to)\s*\b{serial_regex}\b', line, re.IGNORECASE)
                if rng:
                    raw_ranges.append({'start': rng.group(1).upper(), 'end': rng.group(2).upper()})
                    logging.debug(f"Parser: Found standalone range: {raw_ranges[-1]}")
                    continue

        # If data was split (List of Models followed by List of Ranges)
        if models_found and raw_ranges and not model_ranges:
            logging.debug(f"Parser: Attempting to map {len(models_found)} models to {len(raw_ranges)} ranges")
            for idx, model in enumerate(models_found):
                if idx < len(raw_ranges):
                    model_ranges.append({
                        'model': model,
                        'serial_start': raw_ranges[idx]['start'],
                        'serial_end': raw_ranges[idx]['end']
                    })
                    
        return model_ranges

def parse_bulletin_pdf(file_path):
    parser = BulletinParser(file_path)
    return parser.parse()
