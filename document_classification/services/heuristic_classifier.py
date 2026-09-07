from typing import Optional

class HeuristicClassifierService:

    @staticmethod
    def classify(filename: str, file_ext: str, preview_text: str = "") -> Optional[str]:
        fn = filename.upper()
        ext = file_ext.lower()
        text = preview_text.upper() if preview_text else ""

        # =========================
        # CONTRADICTION ENGINE
        # =========================
        def is_contradicted(predicted_type: str) -> bool:
            if not text:
                return False
            
            if predicted_type == "boq":
                # A true BOQ must have quantity-related terms
                required = ["QUANTITY", "RATE", "AMOUNT", "TOTAL", "BOQ", "BILL OF QUANTITIES", "ITEM"]
                if not any(req in text for req in required):
                    return True
                    
            if predicted_type == "contract":
                # A true Contract must have legal/agreement terms
                required = ["AGREEMENT", "CONTRACT", "BETWEEN", "PARTIES", "TERMS", "CONDITIONS", "WITNESSETH"]
                if not any(req in text for req in required):
                    return True
                    
            return False

        # Helper to check contradiction before returning
        def check_and_return(predicted_type: str) -> Optional[str]:
            if is_contradicted(predicted_type):
                print(f"[HEURISTIC] Contradiction detected for '{filename}'. Falling back to LLM.")
                return None
            return predicted_type

        # =========================
        # CAD / DRAWINGS
        # =========================
        if ext in [".dwg", ".dxf"]:
            return check_and_return("drawing")

        drawing_keywords = [
            "DRAWING",
            "PLAN",
            "ELEVATION",
            "SECTION",
            "DETAIL",
            "LAYOUT",
            "GA",
            "GENERAL ARRANGEMENT",
            "SHOP DRAWING",
            "AS-BUILT",
            "FOUNDATION PLAN",
        ]

        if any(k in fn for k in drawing_keywords):
            return check_and_return("drawing")

        # =========================
        # BOQ / ESTIMATION
        # =========================
        boq_keywords = [
            "BOQ",
            "BILL OF QUANTITY",
            "ESTIMATE",
            "COST ESTIMATE",
            "RATE ANALYSIS",
            "QUANTITY TAKEOFF",
            "QTO",
        ]

        if any(k in fn for k in boq_keywords):
            return check_and_return("boq")

        # =========================
        # CONTRACTS
        # =========================
        contract_keywords = [
            "CONTRACT",
            "FIDIC",
            "AGREEMENT",
            "SUBCONTRACT",
            "WORK ORDER",
            "LOA",
            "LETTER OF AWARD",
            "LETTER OF ACCEPTANCE",
        ]

        if any(k in fn for k in contract_keywords):
            return check_and_return("contract")

        # =========================
        # INVOICE
        # =========================
        invoice_keywords = [
            "INVOICE",
            "INV-",
            "TAX INVOICE",
            "BILL",
        ]

        if any(k in fn for k in invoice_keywords):
            return check_and_return("invoice")

        # =========================
        # PURCHASE ORDER
        # =========================
        po_keywords = [
            "PURCHASE ORDER",
            "PO-",
            "PO_",
            "PURCHASE",
        ]

        if any(k in fn for k in po_keywords):
            return check_and_return("purchase_order")

        # =========================
        # RFI
        # =========================
        if "RFI" in fn:
            return check_and_return("rfi")

        # =========================
        # CHANGE ORDER
        # =========================
        change_order_keywords = [
            "CHANGE ORDER",
            "CO-",
            "VARIATION",
            "VO-",
            "VARIATION ORDER",
        ]

        if any(k in fn for k in change_order_keywords):
            return check_and_return("change_order")

        # =========================
        # INSPECTION REPORT
        # =========================
        inspection_keywords = [
            "INSPECTION",
            "ITP",
            "QAQC",
            "QUALITY REPORT",
            "INSPECTION REPORT",
            "SITE INSPECTION",
        ]

        if any(k in fn for k in inspection_keywords):
            return check_and_return("inspection_report")

        # =========================
        # SAFETY
        # =========================
        safety_keywords = [
            "SAFETY",
            "HSE",
            "JSA",
            "RAMS",
            "TOOLBOX",
            "INCIDENT",
            "ACCIDENT",
            "NEAR MISS",
        ]

        if any(k in fn for k in safety_keywords):
            return check_and_return("safety_report")

        # =========================
        # SITE LOG
        # =========================
        site_log_keywords = [
            "SITE LOG",
            "DAILY REPORT",
            "DAILY LOG",
            "SITE DIARY",
            "CONSTRUCTION LOG",
            "PROGRESS LOG",
        ]

        if any(k in fn for k in site_log_keywords):
            return check_and_return("site_log")

        # =========================
        # SCHEDULE
        # =========================
        schedule_keywords = [
            "SCHEDULE",
            "PROGRAMME",
            "BASELINE",
            "PRIMAVERA",
            "MS PROJECT",
            "LOOKAHEAD",
            "WORK PLAN",
        ]

        if any(k in fn for k in schedule_keywords):
            return check_and_return("schedule")

        # =========================
        # SPECIFICATIONS
        # =========================
        spec_keywords = [
            "SPECIFICATION",
            "SPEC",
            "SECTION",
            "TECHNICAL SPECIFICATION",
            "MATERIAL SPECIFICATION",
        ]

        if any(k in fn for k in spec_keywords):
            return check_and_return("specification")

        # =========================
        # MATERIAL SUBMITTAL
        # =========================
        submittal_keywords = [
            "SUBMITTAL",
            "MATERIAL APPROVAL",
            "TECHNICAL DATA SHEET",
            "TDS",
            "PRODUCT DATA",
        ]

        if any(k in fn for k in submittal_keywords):
            return check_and_return("material_submittal")

        # =========================
        # METHOD STATEMENT
        # =========================
        method_keywords = [
            "METHOD STATEMENT",
            "WORK METHOD",
            "EXECUTION PLAN",
        ]

        if any(k in fn for k in method_keywords):
            return check_and_return("method_statement")

        # =========================
        # ENGINEERING CALCULATION
        # =========================
        calc_keywords = [
            "CALCULATION",
            "DESIGN CALCULATION",
            "STRUCTURAL CALC",
            "LOAD CALCULATION",
        ]

        if any(k in fn for k in calc_keywords):
            return check_and_return("engineering_calculation")

        # =========================
        # VENDOR DOCUMENT
        # =========================
        vendor_keywords = [
            "VENDOR",
            "SUPPLIER",
            "MANUFACTURER",
            "CATALOG",
            "BROCHURE",
        ]

        if any(k in fn for k in vendor_keywords):
            return check_and_return("vendor_document")

        # =========================
        # TRANSMITTAL
        # =========================
        transmittal_keywords = [
            "TRANSMITTAL",
            "DOCUMENT TRANSMITTAL",
        ]

        if any(k in fn for k in transmittal_keywords):
            return check_and_return("transmittal")

        # =========================
        # NCR
        # =========================
        ncr_keywords = [
            "NCR",
            "NON CONFORMANCE",
            "NON-CONFORMANCE",
        ]

        if any(k in fn for k in ncr_keywords):
            return check_and_return("ncr")

        # =========================
        # MEETING MINUTES
        # =========================
        mom_keywords = [
            "MOM",
            "MINUTES OF MEETING",
            "MEETING MINUTES",
        ]

        if any(k in fn for k in mom_keywords):
            return check_and_return("meeting_minutes")

        # =========================
        # RFP / PROPOSAL
        # =========================
        rfp_keywords = [
            "RFP",
            "REQUEST FOR PROPOSAL",
            "TENDER",
            "BID DOCUMENT",
        ]

        if any(k in fn for k in rfp_keywords):
            return check_and_return("rfp")

        # =========================
        # FILE TYPE FALLBACKS
        # =========================
        if ext in [".xlsx", ".xls", ".csv"]:
            return check_and_return("spreadsheet")

        if ext in [".eml", ".msg"]:
            return check_and_return("email")

        return None