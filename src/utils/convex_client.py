"""
SteelMind AI Wizard — Convex Database Client
============================================
Handles connection to Convex online database for syncing session history and feedback logs.
Falls back to local memory if CONVEX_URL is not set.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to initialize Convex client
convex_client = None
convex_url = os.getenv("CONVEX_URL")

if convex_url:
    try:
        from convex import ConvexClient
        convex_client = ConvexClient(convex_url)
        logger.info("📡 Connected to Convex online database at: %s", convex_url)
    except Exception as e:
        logger.warning("⚠️ Failed to initialize Convex client: %s. Falling back to local storage.", str(e))
else:
    logger.info("⚠️ CONVEX_URL not set in environment variables — online database sync is disabled.")


def save_session_to_convex(session_id: str, query: str, result: Dict[str, Any]) -> bool:
    """
    Save a diagnostic session to Convex.
    """
    if not convex_client:
        return False
    try:
        timestamp = datetime.now().isoformat()
        convex_client.mutation("sessions:create", {
            "session_id": session_id,
            "query": query,
            "timestamp": timestamp,
            "result": result
        })
        logger.info("📡 Successfully synced session %s to Convex online database", session_id)
        return True
    except Exception as e:
        logger.error("❌ Failed to save session to Convex: %s", str(e))
        return False


def get_history_from_convex() -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve session history from Convex.
    """
    if not convex_client:
        return None
    try:
        records = convex_client.query("sessions:list")
        history = []
        for r in records:
            history.append({
                "session_id": r.get("session_id"),
                "query": r.get("query"),
                "timestamp": r.get("timestamp"),
                "result": r.get("result")
            })
        return history
    except Exception as e:
        logger.error("❌ Failed to fetch session history from Convex: %s", str(e))
        return None


def save_feedback_to_convex(feedback_data: Dict[str, Any]) -> bool:
    """
    Save engineer feedback to Convex.
    """
    if not convex_client:
        return False
    try:
        # Construct arguments aligned with Convex schema
        args = {
            "report_id": feedback_data.get("report_id", "UNKNOWN"),
            "equipment_id": feedback_data.get("equipment_id"),
            "diagnosis_correct": bool(feedback_data.get("diagnosis_correct", True)),
            "actual_fault": feedback_data.get("actual_fault"),
            "outcome": feedback_data.get("outcome", "RESOLVED"),
            "downtime_hours": float(feedback_data.get("downtime_hours", 0.0)),
            "engineer_notes": feedback_data.get("engineer_notes"),
            "timestamp": datetime.now().isoformat()
        }
        convex_client.mutation("feedback:create", args)
        logger.info("📡 Successfully synced feedback for report %s to Convex online database", args["report_id"])
        return True
    except Exception as e:
        logger.error("❌ Failed to save feedback to Convex: %s", str(e))
        return False
