import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  sessions: defineTable({
    session_id: v.string(),
    query: v.string(),
    timestamp: v.string(),
    result: v.any(), // Store the JSON response from diagnostic agent
  }).index("by_session_id", ["session_id"]),

  feedback: defineTable({
    report_id: v.string(),
    equipment_id: v.optional(v.string()),
    diagnosis_correct: v.boolean(),
    actual_fault: v.optional(v.string()),
    outcome: v.string(),
    downtime_hours: v.float64(),
    engineer_notes: v.optional(v.string()),
    timestamp: v.string(),
  }).index("by_report_id", ["report_id"]),
});
