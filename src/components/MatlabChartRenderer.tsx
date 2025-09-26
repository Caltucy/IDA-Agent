"use client";

import { useState, useEffect } from 'react';

interface MatlabData {
  time_series: {
    t: number[];
    y1: number[];
    y2: number[];
    y3: number[];
  };
  categorical: {
    categories: string[];
    values: number[];
  };
  scatter: {
    x: number[];
    y: number[];
  };
  statistics: {
    mean_y1: number;
    std_y1: number;
    mean_y2: number;
    std_y2: number;
    correlation: number;
  };
  timestamp: string;
}

interface MatlabResponse {
  success: boolean;
  data: MatlabData;
  images: { [key: string]: string };
  status: string;
  availableImages: string[];
  timestamp: string;
}

interface MatlabChartRendererProps {
  data?: MatlabResponse;
  onLoadData?: () => void;
}

export default function MatlabChartRenderer({ data, onLoadData }: MatlabChartRendererProps) {
  const [matlabData, setMatlabData] = useState<MatlabResponse | null>(data || null);
  const [loading, setLoading] = useState(!data); // 如果没有传入数据，初始状态为加载中
  const [error, setError] = useState<string | null>(null);

  const loadMatlabData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 首先尝试测试API，如果失败则尝试真实API
      let response = await fetch('/api/chart-data-test');
      if (!response.ok) {
        console.log('测试API失败，尝试真实API...');
        response = await fetch('/api/chart-data');
      }
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '请求失败');
      }
      
      const result = await response.json();
      setMatlabData(result);
      
      if (onLoadData) {
        onLoadData();
      }
    } catch (err: any) {
      setError(err.message);
      console.error('加载MATLAB数据失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 如果没有数据且没有传入数据，自动加载
  useEffect(() => {
    if (!matlabData && !data) {
      loadMatlabData();
    }
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
          <span className="text-gray-300">正在执行MATLAB脚本并生成数据...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 border border-red-500 rounded-lg p-6">
        <div className="text-red-400 mb-4">
          <h3 className="text-lg font-semibold mb-2">MATLAB数据加载失败</h3>
          <p className="text-sm">{error}</p>
        </div>
        <button
          onClick={loadMatlabData}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          重试
        </button>
      </div>
    );
  }

  if (!matlabData) {
    return (
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-6">
        <div className="text-center text-gray-400">
          <p>没有可用的MATLAB数据</p>
          <button
            onClick={loadMatlabData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            加载数据
          </button>
        </div>
      </div>
    );
  }

  const { data: matlabDataContent, images, status, availableImages } = matlabData;

  return (
    <div className="space-y-6">
      {/* 状态信息 */}
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-3">MATLAB执行状态</h3>
        <div className="text-sm text-gray-300">
          <p><strong>执行时间:</strong> {matlabDataContent.timestamp}</p>
          <p><strong>可用图片:</strong> {availableImages.length} 个</p>
          {status && (
            <div className="mt-2">
              <p><strong>状态信息:</strong></p>
              <pre className="text-xs bg-gray-700 p-2 rounded mt-1 whitespace-pre-wrap">
                {status}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* 统计信息 */}
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-3">数据统计</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-gray-700 p-3 rounded">
            <p className="text-gray-400">Y1均值</p>
            <p className="text-white font-semibold">{matlabDataContent.statistics.mean_y1.toFixed(3)}</p>
          </div>
          <div className="bg-gray-700 p-3 rounded">
            <p className="text-gray-400">Y1标准差</p>
            <p className="text-white font-semibold">{matlabDataContent.statistics.std_y1.toFixed(3)}</p>
          </div>
          <div className="bg-gray-700 p-3 rounded">
            <p className="text-gray-400">Y2均值</p>
            <p className="text-white font-semibold">{matlabDataContent.statistics.mean_y2.toFixed(3)}</p>
          </div>
          <div className="bg-gray-700 p-3 rounded">
            <p className="text-gray-400">相关系数</p>
            <p className="text-white font-semibold">{matlabDataContent.statistics.correlation.toFixed(3)}</p>
          </div>
        </div>
      </div>

      {/* 生成的图片 */}
      {availableImages.length > 0 && (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-3">生成的图表</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableImages.map((imageName) => (
              <div key={imageName} className="bg-gray-700 rounded-lg p-3">
                <h4 className="text-sm font-medium text-gray-300 mb-2">
                  {imageName.replace('.png', '').replace('_', ' ').toUpperCase()}
                </h4>
                <div className="bg-white rounded p-2">
                  <img
                    src={images[imageName]}
                    alt={imageName}
                    className="w-full h-auto rounded"
                    style={{ maxHeight: '300px', objectFit: 'contain' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 数据表格 */}
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-3">分类数据</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-600">
                <th className="text-left py-2 text-gray-300">类别</th>
                <th className="text-left py-2 text-gray-300">数值</th>
              </tr>
            </thead>
            <tbody>
              {matlabDataContent.categorical.categories.map((category, index) => (
                <tr key={category} className="border-b border-gray-700">
                  <td className="py-2 text-gray-200">{category}</td>
                  <td className="py-2 text-gray-200">{matlabDataContent.categorical.values[index]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 时间序列数据预览 */}
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-3">时间序列数据预览</h3>
        <div className="text-sm text-gray-300">
          <p>数据点数: {matlabDataContent.time_series.t.length}</p>
          <p>时间范围: {matlabDataContent.time_series.t[0].toFixed(2)} - {matlabDataContent.time_series.t[matlabDataContent.time_series.t.length - 1].toFixed(2)}</p>
          <p>Y1范围: {Math.min(...matlabDataContent.time_series.y1).toFixed(2)} - {Math.max(...matlabDataContent.time_series.y1).toFixed(2)}</p>
          <p>Y2范围: {Math.min(...matlabDataContent.time_series.y2).toFixed(2)} - {Math.max(...matlabDataContent.time_series.y2).toFixed(2)}</p>
        </div>
      </div>

      {/* 刷新按钮 */}
      <div className="flex justify-center">
        <button
          onClick={loadMatlabData}
          className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
        >
          重新执行MATLAB脚本
        </button>
      </div>
    </div>
  );
}
