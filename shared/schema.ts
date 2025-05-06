import { pgTable, text, serial, integer, boolean, jsonb, varchar, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

// Translation documents table
export const documents = pgTable("documents", {
  id: serial("id").primaryKey(),
  originalName: text("original_name").notNull(),
  storagePath: text("storage_path").notNull(),
  originalLanguage: text("original_language"),
  targetLanguage: text("target_language"),
  outputFormat: text("output_format").notNull().default("pdf"),
  status: text("status").notNull().default("pending"),
  translatedPath: text("translated_path"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertDocumentSchema = createInsertSchema(documents).omit({
  id: true,
  createdAt: true,
  translatedPath: true
});

// Languages
export const languages = pgTable("languages", {
  code: text("code").primaryKey(),
  name: text("name").notNull(),
  nativeName: text("native_name"),
  flag: text("flag")
});

export const insertLanguageSchema = createInsertSchema(languages);

// Types
export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

export type InsertDocument = z.infer<typeof insertDocumentSchema>;
export type Document = typeof documents.$inferSelect;

export type InsertLanguage = z.infer<typeof insertLanguageSchema>;
export type Language = typeof languages.$inferSelect;

// Translation request schema for validation
export const translationRequestSchema = z.object({
  documentId: z.number(),
  targetLanguage: z.string(),
  outputFormat: z.enum(["pdf", "txt", "dual"]),
  preserveImages: z.boolean().optional().default(true) // Default to preserving images
});

export type TranslationRequest = z.infer<typeof translationRequestSchema>;
