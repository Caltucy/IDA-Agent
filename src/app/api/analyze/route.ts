import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_API_BASE,
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { query } = body;
    console.log('Received query:', query);

    if (!query) {
        return NextResponse.json({ error: 'Query is required' }, { status: 400 });
    }

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a data analysis expert. Please provide a report and chart data in JSON format. The JSON should have two keys: "report" (a string) and "charts" (an array of objects, where each object has "type" and "data" keys). For example: { "report": "...", "charts": [{ "type": "bar", "data": { "labels": ["X", "Y"], "values": [10, 20] } }] }' },
        { role: 'user', content: query },
      ],
    });

    const responseContent = completion.choices[0].message.content;
    
    if (!responseContent) {
        return NextResponse.json({ error: 'No content received from OpenAI' }, { status: 500 });
    }

    try {
        const jsonData = JSON.parse(responseContent);
        return NextResponse.json(jsonData);
    } catch (e) {
        console.error('Error parsing JSON from OpenAI response:', e);
        // if the model doesn't return valid JSON, just return the text as a report
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