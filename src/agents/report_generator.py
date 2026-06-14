"""
SteelMind AI Wizard — Report Generator Agent
============================================
Compiles all agent outputs into a structured maintenance report.
Generates a properly formatted PDF with headers, bold text, and sections.
"""

import logging
from datetime import datetime
from src.schemas import SteelMindState

logger = logging.getLogger(__name__)


def execute_report_compilation(state: SteelMindState) -> SteelMindState:
    """Generate a structured markdown + PDF report from pipeline state."""
    logger.info("📝 Running Report Generator")

    try:
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        diagnosis    = state.get("diagnosis") or {}
        risk_level   = state.get("risk_level", "UNKNOWN")
        risk_details = state.get("risk_details") or {}
        anomaly_result = state.get("anomaly_result") or {}

        equipment_id   = state.get("equipment_id", "Unknown")
        equipment_type = state.get("equipment_type", "Unknown Type")
        session_id     = state.get("session_id", "default")

        urgency_hours   = risk_details.get("urgency_hours", "N/A")
        fault_identified = diagnosis.get("fault_identified", "No diagnosis available.")
        root_cause       = diagnosis.get("root_cause", "Unknown")
        confidence       = diagnosis.get("confidence", 0.0)
        repair_steps     = diagnosis.get("repair_steps", [])
        immediate_actions = diagnosis.get("immediate_actions", [])
        spare_parts      = diagnosis.get("spare_parts_needed", [])
        sources          = diagnosis.get("sources_cited", [])
        long_term        = diagnosis.get("long_term_recommendations", "")
        change_plan      = diagnosis.get("change_plan", [])
        est_time         = diagnosis.get("estimated_repair_time", "Unknown")
        rul_days         = anomaly_result.get("rul_days", "N/A")
        anomaly_sensor   = anomaly_result.get("anomalous_sensor", "N/A")
        anomaly_score    = anomaly_result.get("anomaly_score", "N/A")

        # ── Quick summary (shown in UI chat log) ────────────
        first_step = repair_steps[0] if repair_steps else "Consult manual."
        summary = (
            f"Fault: {fault_identified}\n"
            f"Risk: {risk_level} — Act within {urgency_hours} hours\n"
            f"Next Step: {first_step}"
        )

        # ── Full markdown (for future use / display) ─────────
        def steps_md(lst):
            return "\n".join(f"{i+1}. {s}" for i, s in enumerate(lst)) if lst else "None."

        spares_md = (
            "\n".join(
                f"- {p.get('quantity',1)}x {p.get('name','?')} (Part#: {p.get('part_number','N/A')})"
                for p in spare_parts
            ) if spare_parts else "None required."
        )
        sources_md = "\n".join(f"- {s}" for s in sources) if sources else "None cited."

        full_report_md = f"""# agentic-ai — Maintenance Report
Report ID: {report_id}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Equipment: {equipment_id} — {equipment_type}
Risk Level: {risk_level}

---
## Executive Summary
{fault_identified}
Recommended to act within {urgency_hours} hours.

---
## Fault Diagnosis
Fault Identified: {fault_identified}
Confidence: {confidence*100:.1f}%
Root Cause: {root_cause}
Estimated Repair Time: {est_time}

---
## Risk Assessment
Final Risk: {risk_level}
Act Within: {urgency_hours} hours
Escalate to Supervisor: {risk_details.get('escalate_to_supervisor', False)}

---
## Immediate Actions
{steps_md(immediate_actions)}

---
## Step-by-Step Repair Plan
{steps_md(repair_steps)}

---
## Safe Component Change Plan
{steps_md(change_plan)}

---
## Spare Parts Required
{spares_md}

---
## Sensor Anomaly & RUL
Remaining Useful Life: {rul_days} days
Anomalous Sensor: {anomaly_sensor}
Anomaly Score: {anomaly_score}

---
## Long-Term Recommendations
{long_term or 'Refer to standard preventive maintenance schedule.'}

---
## Sources Cited
{sources_md}
"""

        # ── Generate PDF ─────────────────────────────────────
        pdf_path = generate_pdf(session_id, report_id, state)

        state["report"] = {
            "summary":        summary,
            "full_report_md": full_report_md,
            "pdf_path":       pdf_path,
            "report_id":      report_id,
            "timestamp":      datetime.now().isoformat(),
        }

        logger.info("   Report generated: %s → %s", report_id, pdf_path)

    except Exception as e:
        logger.error("❌ Report Generator failed: %s", str(e), exc_info=True)
        state["report"] = {
            "summary":        "Report generation failed.",
            "full_report_md": "Report generation failed due to an error.",
            "error":          str(e),
        }

    return state


# ══════════════════════════════════════════════════════════════
# PDF Generation — properly formatted
# ══════════════════════════════════════════════════════════════

def _safe(text: str) -> str:
    """Encode text to latin-1 safely for fpdf2 core fonts."""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def generate_pdf(session_id: str, report_id: str, state: dict) -> str:
    """
    Generate a well-formatted PDF maintenance report using fpdf2.

    Sections use bold headers, separator lines, and proper spacing.
    All text is safely encoded for the Helvetica core font.
    """
    try:
        from fpdf import FPDF
        from pathlib import Path

        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        pdf_path = reports_dir / f"{session_id}.pdf"

        diagnosis     = state.get("diagnosis") or {}
        risk_level    = state.get("risk_level", "UNKNOWN")
        risk_details  = state.get("risk_details") or {}
        anomaly       = state.get("anomaly_result") or {}
        equipment_id  = state.get("equipment_id", "Unknown")
        equipment_type = state.get("equipment_type", "Unknown Type")
        urgency_hours = risk_details.get("urgency_hours", "N/A")

        fault     = diagnosis.get("fault_identified", "No diagnosis.")
        root_cause = diagnosis.get("root_cause", "Unknown")
        confidence = diagnosis.get("confidence", 0.0)
        repair_steps     = diagnosis.get("repair_steps", [])
        immediate_actions = diagnosis.get("immediate_actions", [])
        change_plan      = diagnosis.get("change_plan", [])
        spare_parts      = diagnosis.get("spare_parts_needed", [])
        sources          = diagnosis.get("sources_cited", [])
        long_term        = diagnosis.get("long_term_recommendations", "")
        est_time         = diagnosis.get("estimated_repair_time", "Unknown")
        rul_days         = anomaly.get("rul_days", "N/A")
        anomaly_sensor   = anomaly.get("anomalous_sensor", "N/A")
        anomaly_score    = anomaly.get("anomaly_score", "N/A")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        page_w = pdf.w - 2 * pdf.l_margin

        # ── Helper closures ───────────────────────────────────
        def h1(text: str):
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_fill_color(30, 80, 160)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(page_w, 10, _safe(text), ln=1, fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

        def h2(text: str):
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_fill_color(220, 232, 255)
            pdf.set_text_color(20, 60, 130)
            pdf.cell(page_w, 8, _safe(f"  {text}"), ln=1, fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)

        def kv(label: str, value):
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(55, 7, _safe(f"{label}:"), ln=0)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(page_w - 55, 7, _safe(str(value)))

        def body(text: str):
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(page_w, 6, _safe(str(text)))
            pdf.ln(1)

        def numbered_list(items: list):
            pdf.set_font("Helvetica", "", 10)
            for i, item in enumerate(items, 1):
                pdf.multi_cell(page_w, 6, _safe(f"  {i}. {item}"))
            if not items:
                pdf.multi_cell(page_w, 6, "  None.")

        def bullet_list(items: list):
            pdf.set_font("Helvetica", "", 10)
            for item in items:
                pdf.multi_cell(page_w, 6, _safe(f"  - {item}"))
            if not items:
                pdf.multi_cell(page_w, 6, "  None.")

        def divider():
            pdf.set_draw_color(180, 200, 230)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + page_w, pdf.get_y())
            pdf.ln(2)

        # ── Title Block ───────────────────────────────────────
        h1("agentic-ai  |  Maintenance Diagnostic Report")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(page_w, 5, _safe(f"Report ID: {report_id}    |    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}    |    Tata Steel AI Hackathon 2026"), ln=1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)
        divider()

        # ── Equipment & Risk ──────────────────────────────────
        h2("Equipment & Risk Summary")
        kv("Equipment ID",   equipment_id)
        kv("Equipment Type", equipment_type)
        kv("Risk Level",     risk_level)
        kv("Act Within",     f"{urgency_hours} hours")
        kv("Report ID",      report_id)

        # ── Executive Summary ─────────────────────────────────
        h2("Executive Summary")
        body(f"{fault}  Recommended to act within {urgency_hours} hours.")

        # ── Fault Diagnosis ───────────────────────────────────
        h2("Fault Diagnosis")
        kv("Fault Identified",     fault)
        kv("Root Cause",           root_cause)
        kv("Confidence",           f"{confidence*100:.1f}%")
        kv("Estimated Repair Time", est_time)

        # ── Immediate Actions ─────────────────────────────────
        h2("Immediate Actions")
        numbered_list(immediate_actions)

        # ── Step-by-Step Repair Plan ──────────────────────────
        h2("Step-by-Step Repair Plan")
        numbered_list(repair_steps)

        # ── Safe Component Change Plan ────────────────────────
        if change_plan:
            h2("Safe Component Change Plan (Lockout/Tagout)")
            numbered_list(change_plan)

        # ── Spare Parts ───────────────────────────────────────
        h2("Spare Parts Required")
        if spare_parts:
            bullet_list([
                f"{p.get('quantity',1)}x  {p.get('name','?')}  (Part#: {p.get('part_number','N/A')})"
                for p in spare_parts
            ])
        else:
            body("None required.")

        # ── Sensor Anomaly & RUL ──────────────────────────────
        h2("Sensor Anomaly & Remaining Useful Life")
        kv("RUL Estimate",      f"{rul_days} days")
        kv("Anomalous Sensor",  anomaly_sensor)
        kv("Anomaly Score",     anomaly_score)
        if anomaly.get("normal_range"):
            kv("Normal Range",  anomaly["normal_range"])

        # ── Long-Term Recommendations ─────────────────────────
        h2("Long-Term Recommendations")
        body(long_term or "Refer to standard preventive maintenance schedule.")

        # ── Sources ───────────────────────────────────────────
        h2("Sources Cited")
        bullet_list(sources)

        # ── Footer ────────────────────────────────────────────
        pdf.ln(6)
        divider()
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(page_w, 5,
                 _safe("Generated by agentic-ai  |  Tata Steel AI Hackathon 2026  |  Likhith Sai Parepalli"),
                 ln=1, align="C")

        pdf.output(str(pdf_path))
        logger.info("   PDF generated: %s", pdf_path)
        return str(pdf_path.absolute())

    except Exception as e:
        logger.error("   PDF generation failed: %s", str(e), exc_info=True)
        return ""
