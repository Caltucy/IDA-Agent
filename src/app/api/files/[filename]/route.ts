import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import readline from 'readline';
import * as XLSX from 'xlsx';

const uploadDir = path.join(process.cwd(), 'data');

export async function GET(req: NextRequest, { params }: { params: { filename: string } }) {
  const { filename } = params;
  const filePath = path.join(uploadDir, filename);

  if (!fs.existsSync(filePath)) {
    return NextResponse.json({ error: 'File not found' }, { status: 404 });
  }

  try {
    const fileExtension = path.extname(filename).toLowerCase();
    let lines: string[] = [];

    if (fileExtension === '.xlsx') {
      const fileBuffer = fs.readFileSync(filePath);
      const workbook = XLSX.read(fileBuffer, { type: 'buffer' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 }) as any[][];
      lines = jsonData.slice(0, 10).map(row => row.join(','));
    } else {
      const fileStream = fs.createReadStream(filePath);
      const rl = readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity
      });

      let lineCount = 0;
      for await (const line of rl) {
        lines.push(line);
        lineCount++;
        if (lineCount >= 10) {
          break;
        }
      }
    }

    return NextResponse.json(lines);
  } catch (error) {
    console.error('Error reading file:', error);
    return NextResponse.json({ error: 'Error reading file' }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest, { params }: { params: { filename: string } }) {
  const { filename } = params;
  const filePath = path.join(uploadDir, filename);

  if (!fs.existsSync(filePath)) {
    return NextResponse.json({ error: 'File not found' }, { status: 404 });
  }

  try {
    fs.unlinkSync(filePath);
    return NextResponse.json({ message: 'File deleted successfully' });
  } catch (error) {
    console.error('Error deleting file:', error);
    return NextResponse.json({ error: 'Error deleting file' }, { status: 500 });
  }
}