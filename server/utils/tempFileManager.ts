import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

/**
 * Utility class to manage temporary files
 */
export class TempFileManager {
  private tempDir: string;

  constructor() {
    this.tempDir = path.join(process.cwd(), 'temp');
    this.ensureTempDirExists();
  }

  /**
   * Creates the temp directory if it doesn't exist
   */
  private ensureTempDirExists(): void {
    if (!fs.existsSync(this.tempDir)) {
      fs.mkdirSync(this.tempDir, { recursive: true });
    }
  }

  /**
   * Creates a temporary file with the given prefix and extension
   */
  createTempFile(prefix: string, extension: string): string {
    const fileName = `${prefix}-${uuidv4()}${extension}`;
    return path.join(this.tempDir, fileName);
  }

  /**
   * Writes data to a temporary file and returns the path
   */
  writeTempFile(data: string | Buffer, prefix: string, extension: string): string {
    const filePath = this.createTempFile(prefix, extension);
    fs.writeFileSync(filePath, data);
    return filePath;
  }

  /**
   * Removes a temporary file
   */
  removeTempFile(filePath: string): void {
    if (fs.existsSync(filePath) && filePath.startsWith(this.tempDir)) {
      fs.unlinkSync(filePath);
    }
  }

  /**
   * Cleanup all temporary files
   */
  cleanupAll(): void {
    if (fs.existsSync(this.tempDir)) {
      const files = fs.readdirSync(this.tempDir);
      for (const file of files) {
        fs.unlinkSync(path.join(this.tempDir, file));
      }
    }
  }
}
