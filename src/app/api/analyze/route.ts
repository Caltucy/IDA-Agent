import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import fs from 'fs/promises';
import path from 'path';
import * as XLSX from 'xlsx';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_API_BASE,
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { query, files } = body;
    console.log('Received query:', query, 'and files:', files);

    if (!query) {
        return NextResponse.json({ error: 'Query is required' }, { status: 400 });
    }

    let fileContents = '';
    if (files && files.length > 0) {
      const filePromises = files.map(async (file: string) => {
        const filePath = path.join(process.cwd(), 'data', file);
        try {
          let content = '';
          if (path.extname(file).toLowerCase() === '.xlsx') {
            const fileBuffer = await fs.readFile(filePath);
            const workbook = XLSX.read(fileBuffer, { type: 'buffer' });
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            content = XLSX.utils.sheet_to_csv(worksheet);
          } else {
            content = await fs.readFile(filePath, 'utf-8');
          }
          return `File: ${file}\n${content}`;
        } catch (error) {
          console.error(`Error reading file ${file}:`, error);
          return `File: ${file}\nError reading file`;
        }
      });
      const allFileContents = await Promise.all(filePromises);
      fileContents = allFileContents.join('\n\n');
    }

    const userContent = fileContents ? `${fileContents}\n\n${query}` : query;

    const completion = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL_NAME || 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a data analysis expert. Please provide a report and chart data in JSON format. The JSON should have two keys: "report" (a string) and "charts" (an array of objects, where each object has "type" and "data" keys). For example: { "report": "...", "charts": [{ "type": "bar", "data": { "labels": ["X", "Y"], "values": [10, 20] } }] }' },
        { role: 'user', content: userContent },
      ],
    });

    const responseContent = completion.choices[0].message.content;

    if (!responseContent) {
      return NextResponse.json({ error: "No content received from OpenAI" }, { status: 500 });
    }

    try {
      // 尝试解析JSON响应
      const parsedResponse = JSON.parse(responseContent);
      return NextResponse.json(parsedResponse);
    } catch (parseError) {
      // 如果不是有效的JSON，返回原始文本作为报告
      return NextResponse.json({
        report: responseContent,
        charts: []
      });
    }
  } catch (error) {
    console.error('Error calling OpenAI API:', error);
    if (error instanceof Error) {
        return NextResponse.json({ error: `Failed to analyze data: ${error.message}` }, { status: 500 });
    }
    return NextResponse.json({ error: 'Failed to analyze data' }, { status: 500 });
  }
}