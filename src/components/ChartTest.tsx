"use client";

import { useState } from "react";
import ChartRenderer from "./ChartRenderer";
import { AnalysisResponse } from "../types";

export default function ChartTest() {
  const [testData, setTestData] = useState<AnalysisResponse | null>(null);

  const generateTestData = () => {
    const mockResponse: AnalysisResponse = {
      report: "这是一个测试报告，展示了销售数据的分析结果。从图表中可以看出，Q1和Q2的销售额显著增长，而Q3和Q4保持稳定。",
      charts: [
        {
          type: "bar",
          data: {
            labels: ["Q1", "Q2", "Q3", "Q4"],
            values: [120, 150, 140, 160]
          }
        },
        {
          type: "line",
          data: {
            labels: ["1月", "2月", "3月", "4月", "5月", "6月"],
            values: [100, 120, 110, 130, 125, 140]
          }
        }
      ]
    };
    setTestData(mockResponse);
  };

  return (
    <div className="w-full max-w-6xl mx-auto mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">图表测试</h2>
      
      <button
        onClick={generateTestData}
        className="mb-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        生成测试数据
      </button>

      {testData && (
        <div className="prose dark:prose-invert max-w-none">
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">分析报告</h3>
            <div className="whitespace-pre-wrap bg-gray-50 dark:bg-gray-900 p-4 rounded-md">
              {testData.report}
            </div>
          </div>

          {testData.charts && testData.charts.length > 0 && (
            <div className="mb-6">
              <h3 className="text-xl font-semibold mb-4">数据可视化</h3>
              <ChartRenderer charts={testData.charts} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
