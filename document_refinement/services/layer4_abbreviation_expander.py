import re
from typing import Tuple, List

class Layer4AbbreviationExpander:
    def expand(self, text: str) -> Tuple[str, List[str]]:
        """
        Layer 4: Abbreviation Expander
        Runs on: all strategies.
        Expands abbreviations but keeps original in brackets.
        Avoids expanding inside codes like RFI-023.
        """
        fixes = []
        expanded = text
        
        abbreviations = {
            r'\bRFI\b': 'Request for Information (RFI)',
            r'\bBOQ\b': 'Bill of Quantities (BOQ)',
            r'\bIFC\b': 'Issued for Construction (IFC)',
            r'\bIFR\b': 'Issued for Review (IFR)',
            r'\bIFT\b': 'Issued for Tender (IFT)',
            r'\bMEP\b': 'Mechanical Electrical Plumbing (MEP)',
            r'\bHVAC\b': 'Heating Ventilation Air Conditioning (HVAC)',
            r'\bBIM\b': 'Building Information Modelling (BIM)',
            r'\bEPC\b': 'Engineering Procurement Construction (EPC)',
            r'\bWBS\b': 'Work Breakdown Structure (WBS)',
            r'\bDLP\b': 'Defects Liability Period (DLP)',
            r'\bRC\b(?=\s+(?:concrete|slab|wall|column))': 'Reinforced Concrete (RC)',
            r'(?<![A-Z])\bPC\b': 'Provisional Cost (PC)',
            r'\bPS\b(?=\s+(?:for|item))': 'Provisional Sum (PS)',
            r'\bCO\b(?=\s+(?:No|#|\d))': 'Change Order (CO)',
            r'\bVO\b': 'Variation Order (VO)',
            r'\bQA\b': 'Quality Assurance (QA)',
            r'\bQC\b': 'Quality Control (QC)',
            r'\bPPE\b': 'Personal Protective Equipment (PPE)',
            r'\bITP\b': 'Inspection and Test Plan (ITP)',
            r'\bNDT\b': 'Non-Destructive Testing (NDT)',
            r'\bSBC\b': 'Safe Bearing Capacity (SBC)',
            r'\bLOI\b': 'Letter of Intent (LOI)',
            r'\bNTP\b': 'Notice to Proceed (NTP)',
            r'\bPMC\b': 'Project Management Consultant (PMC)',
            r'\bPO\b(?=\s+(?:No|#|\d))': 'Purchase Order (PO)',
        }
        
        for pattern, repl in abbreviations.items():
            # Use negative lookahead to prevent expanding inside codes like RFI-023
            full_pattern = pattern + r'(?![-/]\d)'
            new_text = re.sub(full_pattern, repl, expanded)
            if new_text != expanded:
                # Get the abbreviation key as a string for the fix list
                key_match = re.search(r'\b([A-Z0-9]+)\b', pattern)
                key_str = key_match.group(1) if key_match else "abbr"
                fixes.append(f"expanded_{key_str}")
                expanded = new_text
                
        return expanded, list(set(fixes))
