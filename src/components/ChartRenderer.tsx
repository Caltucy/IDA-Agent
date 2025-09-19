"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import { Chart } from "../types";

interface ChartRendererProps {
  charts: Chart[];
}

const ChartRenderer = ({ charts }: ChartRendererProps) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {charts.map((chart, index) => {
        const transformedData = chart.data.labels.map((label: string, i: number) => ({
          name: label,
          value: chart.data.values[i],
        }));

        return (
          <div key={index}>
            <h3 className="text-xl font-semibold mb-2 text-center">{chart.type.toUpperCase()} Chart</h3>
            <ResponsiveContainer width="100%" height={300}>
              {chart.type === 'bar' ? (
                <BarChart data={transformedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              ) : (
                <LineChart data={transformedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#82ca9d" />
                </LineChart>
              )}
            </ResponsiveContainer>
          </div>
        );
      })}
    </div>
  );
};

export default ChartRenderer;