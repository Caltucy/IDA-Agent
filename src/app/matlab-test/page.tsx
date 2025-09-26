"use client";

import { useState } from 'react';
import MatlabChartRenderer from '../../components/MatlabChartRenderer';

export default function MatlabTestPage() {
  const [showData, setShowData] = useState(false);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">MATLAB数据集成测试</h1>
        
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">测试说明</h2>
          <div className="text-gray-300 space-y-2">
            <p>• 此页面用于测试MATLAB脚本与Node.js后端的集成</p>
            <p>• 点击下方按钮将执行MATLAB脚本并显示生成的数据和图表</p>
            <p>• 确保MATLAB已安装并在系统PATH中可用</p>
            <p>• 脚本将生成时间序列数据、分类数据和散点图</p>
          </div>
        </div>

        <div className="text-center mb-8">
          <button
            onClick={() => setShowData(!showData)}
            className={`px-8 py-4 rounded-lg text-lg font-medium transition-colors ${
              showData 
                ? "bg-green-600 hover:bg-green-700" 
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {showData ? "隐藏MATLAB数据" : "执行MATLAB脚本并显示数据"}
          </button>
        </div>

        {showData && (
          <div className="bg-gray-800 border border-gray-600 rounded-lg p-6">
            <MatlabChartRenderer />
          </div>
        )}

        <div className="mt-8 bg-gray-800 border border-gray-600 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">技术架构</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-gray-700 p-4 rounded">
              <h4 className="font-semibold text-blue-400 mb-2">MATLAB脚本</h4>
              <p className="text-gray-300">create_data.m</p>
              <p className="text-gray-400 text-xs mt-1">生成数据和图表，保存为JSON和PNG文件</p>
            </div>
            <div className="bg-gray-700 p-4 rounded">
              <h4 className="font-semibold text-green-400 mb-2">Node.js API</h4>
              <p className="text-gray-300">/api/chart-data</p>
              <p className="text-gray-400 text-xs mt-1">执行MATLAB脚本，读取结果并返回数据</p>
            </div>
            <div className="bg-gray-700 p-4 rounded">
              <h4 className="font-semibold text-purple-400 mb-2">前端组件</h4>
              <p className="text-gray-300">MatlabChartRenderer</p>
              <p className="text-gray-400 text-xs mt-1">渲染MATLAB生成的数据和图表</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}






