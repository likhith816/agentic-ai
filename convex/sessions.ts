import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// Get all session history records
export const list = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("sessions").order("desc").take(50);
  },
});

// Get a single session history record by session ID
export const get = query({
  args: { session_id: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("sessions")
      .withIndex("by_session_id", (q) => q.eq("session_id", args.session_id))
      .first();
  },
});

// Save a new session history record
export const create = mutation({
  args: {
    session_id: v.string(),
    query: v.string(),
    timestamp: v.string(),
    result: v.any(),
  },
  handler: async (ctx, args) => {
    // Check if it already exists
    const existing = await ctx.db
      .query("sessions")
      .withIndex("by_session_id", (q) => q.eq("session_id", args.session_id))
      .first();
    
    if (existing) {
      return await ctx.db.patch(existing._id, {
        query: args.query,
        timestamp: args.timestamp,
        result: args.result,
      });
    }

    return await ctx.db.insert("sessions", {
      session_id: args.session_id,
      query: args.query,
      timestamp: args.timestamp,
      result: args.result,
    });
  },
});
