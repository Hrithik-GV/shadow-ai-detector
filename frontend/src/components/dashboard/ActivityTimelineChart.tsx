import React from 'react';
import type { DashboardActivityPoint } from '../../types';

export interface ActivityTimelineChartProps {
  data: DashboardActivityPoint[];
}

export const ActivityTimelineChart: React.FC<ActivityTimelineChartProps> = ({ data }) => {
  if (!data || data.length < 2) {
    return null;
  }

  const values = data.map((d) => d.count ?? d.trafficCount ?? d.aiFlowsCount ?? 0);
  const maxVal = Math.max(...values, 1);
  const minVal = 0;

  const chartHeight = 160;
  const chartWidth = 600;
  const paddingX = 40;
  const paddingY = 25;

  const innerWidth = chartWidth - paddingX * 2;
  const innerHeight = chartHeight - paddingY * 2;

  const points = data.map((d, index) => {
    const val = d.count ?? d.trafficCount ?? d.aiFlowsCount ?? 0;
    const x = paddingX + (index / (data.length - 1)) * innerWidth;
    const y = paddingY + innerHeight - ((val - minVal) / (maxVal - minVal)) * innerHeight;
    return { x, y, val, label: d.timestamp };
  });

  const polylinePoints = points.map((p) => `${p.x},${p.y}`).join(' ');

  return (
    <div className="space-y-2 font-mono text-xs">
      <div className="flex items-center justify-between text-[#9A9A91] text-[11px]">
        <span>LIVE TELEMETRY ACTIVITY OVER TIME</span>
        <span className="text-[#FFCC00]">PEAK: {maxVal.toLocaleString()}</span>
      </div>

      <div className="w-full bg-[#0D0D0D] border border-[#333330] p-3 overflow-x-auto">
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="w-full h-auto min-w-[480px]"
          shapeRendering="crispEdges"
        >
          {/* Horizontal grid lines */}
          <line
            x1={paddingX}
            y1={paddingY}
            x2={chartWidth - paddingX}
            y2={paddingY}
            stroke="#333330"
            strokeDasharray="2 2"
          />
          <line
            x1={paddingX}
            y1={paddingY + innerHeight / 2}
            x2={chartWidth - paddingX}
            y2={paddingY + innerHeight / 2}
            stroke="#333330"
            strokeDasharray="2 2"
          />
          <line
            x1={paddingX}
            y1={paddingY + innerHeight}
            x2={chartWidth - paddingX}
            y2={paddingY + innerHeight}
            stroke="#333330"
          />

          {/* Stepped / connected line */}
          <polyline
            fill="none"
            stroke="#FFCC00"
            strokeWidth="2"
            points={polylinePoints}
          />

          {/* Square pixel data points */}
          {points.map((p, idx) => (
            <g key={idx}>
              <rect
                x={p.x - 3}
                y={p.y - 3}
                width={6}
                height={6}
                fill="#FFCC00"
                stroke="#0D0D0D"
                strokeWidth={1}
              />
            </g>
          ))}

          {/* Y Axis labels */}
          <text x={paddingX - 6} y={paddingY + 4} fill="#9A9A91" fontSize="9" textAnchor="end">
            {maxVal}
          </text>
          <text x={paddingX - 6} y={paddingY + innerHeight} fill="#9A9A91" fontSize="9" textAnchor="end">
            0
          </text>

          {/* X Axis First and Last timestamps */}
          {points.length > 0 && (
            <>
              <text x={paddingX} y={chartHeight - 6} fill="#9A9A91" fontSize="8" textAnchor="start">
                {points[0].label}
              </text>
              <text
                x={chartWidth - paddingX}
                y={chartHeight - 6}
                fill="#9A9A91"
                fontSize="8"
                textAnchor="end"
              >
                {points[points.length - 1].label}
              </text>
            </>
          )}
        </svg>
      </div>
    </div>
  );
};
