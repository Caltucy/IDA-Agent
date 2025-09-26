"use client";

import { useState, useEffect } from "react";
import { Chart } from "../types";

interface ChartRendererProps {
  charts: Chart[];
}

const ChartRenderer = ({ charts }: ChartRendererProps) => {
  const [chartImages, setChartImages] = useState<{[key: number]: string}>({});
  const [loadingStates, setLoadingStates] = useState<{[key: number]: boolean}>({});

  // 生成图表图片
  const generateChartImage = async (chart: Chart, index: number) => {
    setLoadingStates(prev => ({ ...prev, [index]: true }));
    
    try {
      const formData = new FormData();
      formData.append('chart_data', JSON.stringify(chart.data));
      formData.append('chart_type', chart.type || 'bar');
      formData.append('title', chart.title || '图表');

      const response = await fetch('/api/generate-chart', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        setChartImages(prev => ({ ...prev, [index]: imageUrl }));
      } else {
        console.error('图表生成失败');
      }
    } catch (error) {
      console.error('生成图表时出错:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, [index]: false }));
    }
  };

  // 当charts变化时，生成所有图表图片
  useEffect(() => {
    charts.forEach((chart, index) => {
      if (!chartImages[index] && !loadingStates[index]) {
        generateChartImage(chart, index);
      }
    });
  }, [charts]);

  // 清理图片URL
  useEffect(() => {
    return () => {
      Object.values(chartImages).forEach(url => {
        if (url) URL.revokeObjectURL(url);
      });
    };
  }, [chartImages]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {charts.map((chart, index) => (
        <div key={index} className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-base md:text-lg font-semibold mb-4 text-center text-gray-200">
            {chart.title || (chart.type === 'bar' ? '柱状图' : chart.type === 'line' ? '折线图' : '图表')}
          </h3>
          
          {loadingStates[index] ? (
            <div className="flex items-center justify-center h-64 bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-300"></div>
                <span className="text-gray-300">正在生成图表...</span>
              </div>
            </div>
          ) : chartImages[index] ? (
            <div className="flex justify-center">
              <img 
                src={chartImages[index]} 
                alt={chart.title || '图表'} 
                className="max-w-full h-auto rounded-lg shadow-sm"
                style={{ maxHeight: '400px' }}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 bg-gray-700 rounded-lg">
              <span className="text-gray-400">图表加载失败</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ChartRenderer;