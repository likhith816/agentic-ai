"""
SteelMind AI Wizard — Feedback Agent
======================================
Captures engineer feedback and stores it in SQLite.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("src/data/steelmind_feedback.db")

def init_db():
    """Initialize SQLite database tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT NOT NULL,
            diagnosis_correct BOOLEAN,
            actual_fault TEXT,
            outcome TEXT,
            downtime_hours REAL,
            engineer_notes TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def update_knowledge_base(feedback: dict):
    """
    Update the FAISS knowledge base with the corrected diagnostic feedback.
    Appends the correction as a document so that subsequent RAG searches retrieve it.
    """
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    from src.utils.embeddings import get_embeddings
    
    faiss_path = "src/knowledge_base/faiss_index"
    
    try:
        logger.info(f"🧠 Updating FAISS index with corrected feedback for {feedback.get('report_id')}")
        embeddings = get_embeddings()
        
        # Load existing index
        if not Path(faiss_path).exists():
            logger.error(f"FAISS index not found at {faiss_path} — cannot append feedback.")
            return
            
        vectorstore = FAISS.load_local(
            faiss_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        
        # Construct document content
        content = (
            f"Historical Correction Event:\n"
            f"- Equipment ID: {feedback.get('equipment_id', 'Unknown')}\n"
            f"- Reported Fault: {feedback.get('actual_fault', 'Unknown')}\n"
            f"- Corrective Action Taken: {feedback.get('actual_steps_taken', 'Refer to manual')}\n"
            f"- Outcome: {feedback.get('outcome', 'RESOLVED')}\n"
            f"- Engineer Notes: {feedback.get('engineer_notes', 'None')}"
        )
        
        doc = Document(
            page_content=content,
            metadata={
                "source": f"feedback_{feedback.get('report_id', 'unknown')}.txt",
                "page": 0,
                "chunk_id": f"fb_{feedback.get('report_id', 'unknown')}"
            }
        )
        
        # Add to vector store and save
        vectorstore.add_documents([doc])
        vectorstore.save_local(faiss_path)
        logger.info(f"✅ FAISS index updated and saved to {faiss_path}")
        
    except Exception as e:
        logger.error(f"❌ Failed to update FAISS index: {str(e)}", exc_info=True)

def execute_feedback_processing(feedback_input: dict) -> dict:
    """Store engineer feedback in SQLite."""
    logger.info("🗣️ Running Feedback Agent")
    init_db()
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("""
            INSERT INTO feedback (
                report_id, diagnosis_correct, actual_fault,
                outcome, downtime_hours, engineer_notes,
                timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback_input.get("report_id", "UNKNOWN"),
            feedback_input.get("diagnosis_correct", True),
            feedback_input.get("actual_fault", ""),
            feedback_input.get("outcome", "RESOLVED"),
            feedback_input.get("downtime_hours", 0.0),
            feedback_input.get("engineer_notes", ""),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        knowledge_updated = False
        if not feedback_input.get("diagnosis_correct", True) and feedback_input.get("actual_fault"):
            update_knowledge_base(feedback_input)
            knowledge_updated = True
            
        feedback_id = f"FB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"✅ Feedback saved: {feedback_id}")
        
        return {
            "feedback_id": feedback_id,
            "saved": True,
            "knowledge_updated": knowledge_updated
        }
        
    except Exception as e:
        logger.error(f"❌ Feedback Agent failed: {str(e)}")
        return {
            "saved": False,
            "error": str(e)
        }
