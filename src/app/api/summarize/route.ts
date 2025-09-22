import { NextRequest, NextResponse } from 'next/server';
import { app } from '@/lib/agent';
import { AIMessage, HumanMessage } from '@langchain/core/messages';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { filename } = body;

    if (!filename) {
      return NextResponse.json({ error: 'Filename is required' }, { status: 400 });
    }

    const inputs = {
      messages: [new HumanMessage(`Please summarize the file: ${filename}`)],
      filename,
    };

    const result = await app.invoke(inputs);

    // 使用 Array.isArray() 作为类型守卫
    if (result.messages && Array.isArray(result.messages)) {
      // 在这个 if 代码块内部，TypeScript 知道 result.messages 肯定是一个数组
      const lastMessage = result.messages[result.messages.length - 1];
      console.log(lastMessage);
      if (lastMessage instanceof AIMessage) {
      return NextResponse.json({ summary: lastMessage.content });
      }
    } else {
    // 处理 messages 不存在或者是其他类型的情况
      console.log("No messages found or the format is incorrect.");
    }

    return NextResponse.json({ error: 'Failed to get a summary' }, { status: 500 });
  } catch (error) {
    console.error('Error summarizing file:', error);
    return NextResponse.json({ error: 'Error summarizing file' }, { status: 500 });
  }
}