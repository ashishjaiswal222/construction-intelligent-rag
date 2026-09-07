import re

class TextPreprocessor:
    CONSTRUCTION_ABBREVIATIONS = {
        r'\bRFI\b': 'Request for Information RFI',
        r'\bBOQ\b': 'Bill of Quantities BOQ',
        r'\bIFC\b': 'Issued for Construction IFC',
        r'\bIFR\b': 'Issued for Review IFR',
        r'\bIFT\b': 'Issued for Tender IFT',
        r'\bEPC\b': 'Engineering Procurement Construction EPC',
        r'\bWBS\b': 'Work Breakdown Structure WBS',
        r'\bDLP\b': 'Defects Liability Period DLP',
        r'\bNEC\b': 'New Engineering Contract NEC',
        r'\bMEP\b': 'Mechanical Electrical Plumbing MEP',
        r'\bHVAC\b': 'Heating Ventilation Air Conditioning HVAC',
        r'\bBIM\b': 'Building Information Modelling BIM',
        r'\bRC\b': 'Reinforced Concrete RC',
        r'\bPC\b(?!\s+[A-Z])': 'Provisional Cost PC',
        r'\bPS\b': 'Provisional Sum PS',
        r'\bCO\b': 'Change Order CO',
        r'\bPO\b': 'Purchase Order PO',
        r'\bNOS\b|\bNos\b': 'numbers',
        r'\bNR\b|\bNr\b': 'number',
        r'\bITP\b': 'Inspection Test Plan ITP',
        r'\bNCR\b': 'Non-Conformance Report NCR',
        r'\bQA\b': 'Quality Assurance QA',
        r'\bQC\b': 'Quality Control QC',
        r'\bFIDIC\b': 'Federation Internationale des Ingenieurs-Conseils FIDIC contract',
        r'\bEOT\b': 'Extension of Time EOT',
        r'\bVO\b': 'Variation Order VO',
        r'\bHSE\b': 'Health Safety and Environment HSE',
        r'\bO&M\b': 'Operations and Maintenance O&M',
        r'\bAFC\b': 'Approved for Construction AFC',
        r'\bASB\b': 'As-Built ASB',
        r'\bFFL\b': 'Finished Floor Level FFL',
        r'\bSSL\b': 'Structural Slab Level SSL',
        r'\bNGL\b': 'Natural Ground Level NGL',
        r'\bRL\b': 'Reduced Level RL',
        r'\bROW\b': 'Right of Way ROW',
        r'\bFCL\b': 'Finished Ceiling Level FCL',
        r'\bTBM\b': 'Temporary Benchmark TBM',
        r'\bPPE\b': 'Personal Protective Equipment PPE',
        r'\bPT\b': 'Post-Tensioned PT',
        r'\bMEPF\b': 'Mechanical Electrical Plumbing and Firefighting MEPF',
        r'\bFA\b': 'Fire Alarm FA',
        r'\bFP\b': 'Fire Protection FP',
        r'\bCHW\b': 'Chilled Water CHW',
        r'\bDB\b': 'Distribution Board DB',
        r'\bSMDB\b': 'Sub Main Distribution Board SMDB',
        r'\bMDB\b': 'Main Distribution Board MDB',
        r'\bLV\b': 'Low Voltage LV',
        r'\bMV\b': 'Medium Voltage MV',
        r'\bHV\b': 'High Voltage HV',
        r'\bELV\b': 'Extra Low Voltage ELV',
        r'\bCCTV\b': 'Closed-Circuit Television CCTV',
        r'\bPA\b': 'Public Address PA',
        r'\bBMS\b': 'Building Management System BMS',
        r'\bAHU\b': 'Air Handling Unit AHU',
        r'\bFCU\b': 'Fan Coil Unit FCU',
        r'\bVAV\b': 'Variable Air Volume VAV',
        r'\bVRF\b': 'Variable Refrigerant Flow VRF',
        r'\bGI\b': 'Galvanized Iron GI',
        r'\bUPVC\b': 'Unplasticized Polyvinyl Chloride UPVC',
        r'\bHDPE\b': 'High-Density Polyethylene HDPE',
        r'\bDI\b': 'Ductile Iron DI',
        r'\bRCC\b': 'Reinforced Cement Concrete RCC',
        r'\bPCC\b': 'Plain Cement Concrete PCC',
        r'\bDPC\b': 'Damp Proof Course DPC',
        r'\bEPDM\b': 'Ethylene Propylene Diene Monomer EPDM',
        r'\bGFC\b': 'Good for Construction GFC',
        r'\bGPR\b': 'Ground Penetrating Radar GPR',
        r'\bTOR\b': 'Terms of Reference TOR',
        r'\bLOI\b': 'Letter of Intent LOI',
        r'\bLOA\b': 'Letter of Award LOA',
    }

    UNIT_SYNONYMS = {
        r'\bm3\b|\bm³\b|\bcbm\b|\bCBM\b|\bcum\b|\bCUM\b': 'cubic metres m3',
        r'\bm2\b|\bm²\b|\bsqm\b|\bSQM\b': 'square metres m2',
        r'\bln\.?m\b|\bLm\b|\blm\b|\bRM\b|\brm\b': 'linear metres',
        r'\bMT\b|\bmt\b(?!\s*[A-Z])': 'metric tonnes',
        r'\bkg\b|\bKg\b|\bKG\b': 'kilograms',
        r'\bMPa\b': 'megapascals MPa N/mm2',
        r'\bN/mm2\b|\bN/mm²\b': 'N/mm2 megapascals',
        r'\bkN\b': 'kilonewtons kN',
        r'\bkNm\b': 'kilonewton metres kNm moment',
        r'\bmm\b': 'millimeters mm',
        r'\bcm\b': 'centimeters cm',
        r'\bdia\b|Ø': 'diameter',
        r'\blts\b|\bltrs\b|\bl\b(?!\s+[A-Z])': 'liters',
        r'\bpsi\b': 'pounds per square inch psi',
        r'\bcfm\b': 'cubic feet per minute cfm',
        r'\bgpm\b': 'gallons per minute gpm',
        r'\bkW\b': 'kilowatts kW',
        r'\bkVA\b': 'kilovolt-amperes kVA',
    }

    GRADE_SYNONYMS = {
        r'\bC20\b': 'Grade C20 concrete blinding 20 N/mm2',
        r'\bC25\b': 'Grade C25 concrete 25 N/mm2 compressive strength',
        r'\bC30\b': 'Grade C30 concrete 30 N/mm2 compressive strength',
        r'\bC35\b': 'Grade C35 concrete 35 N/mm2 compressive strength',
        r'\bC40\b': 'Grade C40 concrete 40 N/mm2 compressive strength',
        r'\bC45\b': 'Grade C45 concrete 45 N/mm2 compressive strength',
        r'\bC50\b': 'Grade C50 concrete 50 N/mm2 compressive strength',
        r'\bC60\b': 'Grade C60 concrete 60 N/mm2 compressive strength',
        r'\bC80\b': 'Grade C80 concrete 80 N/mm2 compressive strength',
        r'\bFe415\b': 'Grade Fe415 rebar reinforcement steel 415 N/mm2',
        r'\bFe500\b': 'Grade Fe500 rebar reinforcement steel 500 N/mm2',
        r'\bFe500D\b': 'Grade Fe500D ductile rebar reinforcement steel',
        r'\bFe550\b': 'Grade Fe550 rebar reinforcement steel 550 N/mm2',
        r'\bFe600\b': 'Grade Fe600 rebar reinforcement steel 600 N/mm2',
        r'\bHYSD\b': 'High Yield Strength Deformed bar HYSD rebar',
        r'\bTMT\b': 'Thermo Mechanically Treated TMT rebar steel',
    }

    DOC_TYPE_PREFIX = {
        'contract': 'Construction contract legal clause: ',
        'boq': 'Construction bill of quantities item: ',
        'drawing': 'Construction technical drawing: ',
        'specification': 'Construction technical specification: ',
        'rfi': 'Construction request for information: ',
        'site_log': 'Construction site daily log entry: ',
        'inspection': 'Construction inspection report: ',
        'safety': 'Construction safety report: ',
        'change_order': 'Construction change order: ',
        'invoice': 'Construction invoice payment certificate: ',
    }

    def preprocess(self, text: str, doc_type: str) -> str:
        """
        Full preprocessing pipeline.
        NEVER raises — returns original text on any failure.
        """
        if not text:
            return ''
        
        try:
            processed = text
            
            # Apply abbreviation expansions
            for pattern, expansion in self.CONSTRUCTION_ABBREVIATIONS.items():
                processed = re.sub(pattern, expansion, processed)
                
            # Apply unit normalisation
            for pattern, expansion in self.UNIT_SYNONYMS.items():
                processed = re.sub(pattern, expansion, processed)
                
            # Apply grade synonyms
            for pattern, expansion in self.GRADE_SYNONYMS.items():
                processed = re.sub(pattern, expansion, processed)
            
            # Prefix injection
            prefix = self.DOC_TYPE_PREFIX.get(doc_type, 'Construction document: ')
            processed = prefix + processed
            
            # Collapse whitespace
            processed = re.sub(r'\s+', ' ', processed).strip()
            return processed
        except Exception:
            return text

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate: len(text) / 4"""
        if not text:
            return 0
        return max(1, len(text) // 4)
