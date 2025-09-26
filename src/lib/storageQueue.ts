/**
 * 存储队列工具 - 解决localStorage并发写入问题
 * 使用队列机制确保对同一个key的写入操作按顺序执行
 */

interface QueueItem {
  key: string;
  value: any;
  resolve: (success: boolean) => void;
}

class StorageQueue {
  private queue: QueueItem[] = [];
  private processing: boolean = false;
  private static instance: StorageQueue;

  private constructor() {}

  // 单例模式
  public static getInstance(): StorageQueue {
    if (!StorageQueue.instance) {
      StorageQueue.instance = new StorageQueue();
    }
    return StorageQueue.instance;
  }

  /**
   * 将数据添加到队列中
   * @param key localStorage的键
   * @param value 要存储的值
   * @returns Promise，成功时返回true
   */
  public enqueue(key: string, value: any): Promise<boolean> {
    console.log(`[StorageQueue] 添加到队列: ${key}, 数据长度: ${Array.isArray(value) ? value.length : '非数组'}`);
    return new Promise((resolve) => {
      this.queue.push({ key, value, resolve });
      console.log(`[StorageQueue] 当前队列长度: ${this.queue.length}`);
      this.processQueue();
    });
  }

  /**
   * 处理队列中的项目
   */
  private processQueue(): void {
    if (this.processing || this.queue.length === 0) return;
    
    this.processing = true;
    const { key, value, resolve } = this.queue.shift()!;
    
    try {
      console.log(`[StorageQueue] 正在处理: ${key}, 数据长度: ${Array.isArray(value) ? value.length : '非数组'}`);
      localStorage.setItem(key, JSON.stringify(value));
      console.log(`[StorageQueue] 成功保存到localStorage: ${key}`);
      resolve(true);
    } catch (e) {
      console.error('[StorageQueue] 写入localStorage失败:', e);
      resolve(false);
    } finally {
      this.processing = false;
      // 使用setTimeout确保在当前执行栈清空后再处理下一个项目
      setTimeout(() => {
        console.log(`[StorageQueue] 队列剩余项目: ${this.queue.length}`);
        this.processQueue();
      }, 0);
    }
  }

  /**
   * 同步获取localStorage中的值
   * @param key localStorage的键
   * @returns 解析后的值，如果不存在或解析失败则返回null
   */
  public getItem(key: string): any {
    try {
      console.log(`[StorageQueue] 读取localStorage: ${key}`);
      const item = localStorage.getItem(key);
      if (item) {
        const parsed = JSON.parse(item);
        console.log(`[StorageQueue] 成功读取: ${key}, 数据长度: ${Array.isArray(parsed) ? parsed.length : '非数组'}`);
        return parsed;
      }
      console.log(`[StorageQueue] ${key} 不存在或为空`);
      return null;
    } catch (e) {
      console.error(`[StorageQueue] 读取localStorage失败: ${key}`, e);
      return null;
    }
  }
}

export const storageQueue = StorageQueue.getInstance();