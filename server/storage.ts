import { documents, languages, users, type Document, type InsertDocument, type User, type InsertUser, type Language, type InsertLanguage } from "@shared/schema";

// Interface for all storage operations
export interface IStorage {
  // User operations
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Document operations
  getDocument(id: number): Promise<Document | undefined>;
  createDocument(document: InsertDocument): Promise<Document>;
  updateDocument(id: number, updates: Partial<Document>): Promise<Document>;
  deleteDocument(id: number): Promise<boolean>;
  getDocuments(): Promise<Document[]>;
  
  // Language operations
  getLanguage(code: string): Promise<Language | undefined>;
  getLanguages(): Promise<Language[]>;
  addLanguage(language: InsertLanguage): Promise<Language>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private docsMap: Map<number, Document>;
  private languagesMap: Map<string, Language>;
  currentUserId: number;
  currentDocId: number;

  constructor() {
    this.users = new Map();
    this.docsMap = new Map();
    this.languagesMap = new Map();
    this.currentUserId = 1;
    this.currentDocId = 1;
  }

  // User methods
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.currentUserId++;
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  // Document methods
  async getDocument(id: number): Promise<Document | undefined> {
    return this.docsMap.get(id);
  }

  async createDocument(insertDoc: InsertDocument): Promise<Document> {
    const id = this.currentDocId++;
    const now = new Date();
    const document: Document = {
      ...insertDoc,
      id,
      createdAt: now,
    };
    this.docsMap.set(id, document);
    return document;
  }

  async updateDocument(id: number, updates: Partial<Document>): Promise<Document> {
    const document = this.docsMap.get(id);
    if (!document) {
      throw new Error(`Document with ID ${id} not found`);
    }

    const updatedDocument = {
      ...document,
      ...updates,
    };

    this.docsMap.set(id, updatedDocument);
    return updatedDocument;
  }

  async deleteDocument(id: number): Promise<boolean> {
    return this.docsMap.delete(id);
  }

  async getDocuments(): Promise<Document[]> {
    return Array.from(this.docsMap.values());
  }

  // Language methods
  async getLanguage(code: string): Promise<Language | undefined> {
    return this.languagesMap.get(code);
  }

  async getLanguages(): Promise<Language[]> {
    return Array.from(this.languagesMap.values());
  }

  async addLanguage(language: InsertLanguage): Promise<Language> {
    this.languagesMap.set(language.code, language as Language);
    return language as Language;
  }
}

export const storage = new MemStorage();
