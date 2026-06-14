import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const create = mutation({
  args: {
    report_id: v.string(),
    equipment_id: v.optional(v.string()),
    diagnosis_correct: v.boolean(),
    actual_fault: v.optional(v.string()),
    outcome: v.string(),
    downtime_hours: v.float64(),
    engineer_notes: v.optional(v.string()),
    timestamp: v.string(),
  },
  handler: async (ctx, args) => {
    // Check if feedback already exists for this report
    const existing = await ctx.db
      .query("feedback")
      .withIndex("by_report_id", (q) => q.eq("report_id", args.report_id))
      .first();

    if (existing) {
      return await ctx.db.patch(existing._id, args);
    }

    return await ctx.db.insert("feedback", args);
  },
});

export const list = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("feedback").order("desc").take(50);
  },
});
