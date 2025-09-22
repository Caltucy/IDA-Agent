import { z } from 'zod';
import { StructuredTool } from '@langchain/core/tools';
import fs from 'fs';
import path from 'path';

const uploadDir = path.join(process.cwd(), 'uploads');

class FileReaderTool extends StructuredTool {
  name = 'file-reader';
  description = 'Reads the content of a file.';
  schema = z.object({
    filename: z.string().describe('The name of the file to read.'),
  });

  async _call({ filename }: z.infer<typeof this.schema>) {
    const filePath = path.join(uploadDir, filename);
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      return content;
    } catch (error) {
      return `Error reading file: ${error}`;
    }
  }
}

export { FileReaderTool };