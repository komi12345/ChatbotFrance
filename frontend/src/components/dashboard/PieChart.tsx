"use client";

import { useState, useEffect } from "react";
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface StatusData {
  status: string;
  count: number;
  percentage: number;
}

interface PieChartProps {
  data: StatusData[];
  title?: string;
  isLoading?: boolean;
}

// Couleurs pour chaque statut - palette émeraude
const STATUS_COLORS: Record<string, string> = {
  "Envoyés": "#3B82F6",    // Bleu
  "Délivrés": "#10B981",   // Vert émeraude
  "Lus": "#059669",        // Vert foncé
  "Échoués": "#EF4444",    // Rouge
  "En attente": "#F59E0B", // Orange
};

function useScreenSize() {
  const [screenSize, setScreenSize] = useState<"mobile" | "tablet" | "desktop">("desktop");

  useEffect(() => {
    const checkSize = () => {
      if (window.innerWidth < 640) {
        setScreenSize("mobile");
      } else if (window.innerWidth < 1024) {
        setScreenSize("tablet");
      } else {
        setScreenSize("desktop");
      }
    };

    checkSize();
    window.addEventListener("resize", checkSize);
    return () => window.removeEventListener("resize", checkSize);
  }, []);

  return screenSize;
}

function CustomLabel(props: {
  cx?: number;
  cy?: number;
  midAngle?: number;
  innerRadius?: number;
  outerRadius?: number;
  percent?: number;
  isMobile?: boolean;
}) {
  const { cx = 0, cy = 0, midAngle = 0, innerRadius = 0, outerRadius = 0, percent = 0, isMobile = false } = props;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  const threshold = isMobile ? 0.10 : 0.05;
  if (percent < threshold) return null;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      className="font-medium"
      style={{ fontSize: isMobile ? "10px" : "12px" }}
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

export function PieChart({
  data,
  title = "Répartition des statuts",
  isLoading = false,
}: PieChartProps) {
  const screenSize = useScreenSize();
  const isMobile = screenSize === "mobile";

  const outerRadius = isMobile ? 70 : 100;
  const innerRadius = isMobile ? 40 : 60; // Donut chart

  if (isLoading) {
    return (
      <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
        <h3 className="text-lg font-semibold text-[#111827] mb-4">{title}</h3>
        <div className="h-[250px] sm:h-[300px] flex items-center justify-center">
          <div className="w-36 h-36 sm:w-48 sm:h-48 bg-[#F3F4F6] animate-pulse rounded-full" />
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
        <h3 className="text-lg font-semibold text-[#111827] mb-4">{title}</h3>
        <div className="h-[250px] sm:h-[300px] flex items-center justify-center">
          <p className="text-[#6B7280] text-sm">Aucune donnée disponible</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
      <h3 className="text-lg font-semibold text-[#111827] mb-4">{title}</h3>
      <div className="h-[250px] sm:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsPieChart>
            <Pie
              data={data as Array<StatusData & { [key: string]: unknown }>}
              cx="50%"
              cy="45%"
              labelLine={false}
              label={(props) => <CustomLabel {...props} isMobile={isMobile} />}
              outerRadius={outerRadius}
              innerRadius={innerRadius}
              fill="#8884d8"
              dataKey="count"
              nameKey="status"
              strokeWidth={2}
              stroke="#FFFFFF"
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={STATUS_COLORS[entry.status] || "#6B7280"}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "#FFFFFF",
                border: "1px solid #E5E7EB",
                borderRadius: "12px",
                fontSize: isMobile ? "12px" : "14px",
                boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
              }}
              formatter={(value: number, name: string) => [
                `${value} messages (${data.find(d => d.status === name)?.percentage || 0}%)`,
                name,
              ]}
            />
            <Legend
              verticalAlign="bottom"
              height={isMobile ? 48 : 36}
              wrapperStyle={{ fontSize: isMobile ? "10px" : "12px", paddingTop: "10px" }}
              iconSize={isMobile ? 8 : 14}
              iconType="circle"
              formatter={(value: string) => (
                <span className="text-[#111827]">{value}</span>
              )}
            />
          </RechartsPieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default PieChart;
