"use client";

import { useState, useEffect } from "react";
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";

interface DailyData {
  date: string;
  sent: number;
  delivered: number;
  read: number;
  failed: number;
}

interface LineChartProps {
  data: DailyData[];
  title?: string;
  isLoading?: boolean;
}

function formatDate(dateStr: string, short: boolean = false): string {
  const date = new Date(dateStr);
  if (short) {
    return date.toLocaleDateString("fr-FR", { day: "2-digit" });
  }
  return date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
}

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

export function LineChart({ data, title = "Évolution des envois", isLoading = false }: LineChartProps) {
  const screenSize = useScreenSize();
  const isMobile = screenSize === "mobile";
  const isTablet = screenSize === "tablet";

  if (isLoading) {
    return (
      <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
        <h3 className="text-lg font-semibold text-[#111827] mb-4">{title}</h3>
        <div className="h-[250px] sm:h-[300px] bg-[#F3F4F6] animate-pulse rounded-xl" />
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

  const margins = isMobile
    ? { top: 10, right: 10, left: 0, bottom: 5 }
    : isTablet
    ? { top: 10, right: 20, left: 10, bottom: 5 }
    : { top: 10, right: 30, left: 20, bottom: 5 };

  return (
    <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
      <h3 className="text-lg font-semibold text-[#111827] mb-4">{title}</h3>
      <div className="h-[250px] sm:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={margins}>
            <defs>
              <linearGradient id="colorSent" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorDelivered" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="date"
              tickFormatter={(val) => formatDate(val, isMobile)}
              tick={{ fill: "#6B7280", fontSize: isMobile ? 10 : 12 }}
              tickMargin={isMobile ? 5 : 10}
              interval={isMobile ? 1 : 0}
              axisLine={{ stroke: "#E5E7EB" }}
              tickLine={{ stroke: "#E5E7EB" }}
            />
            <YAxis
              tick={{ fill: "#6B7280", fontSize: isMobile ? 10 : 12 }}
              width={isMobile ? 30 : 40}
              tickFormatter={(val) => (isMobile && val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)}
              axisLine={{ stroke: "#E5E7EB" }}
              tickLine={{ stroke: "#E5E7EB" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#FFFFFF",
                border: "1px solid #E5E7EB",
                borderRadius: "12px",
                fontSize: isMobile ? "12px" : "14px",
                boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
              }}
              labelFormatter={(val) => formatDate(val as string, false)}
            />
            <Legend
              wrapperStyle={{ fontSize: isMobile ? "10px" : "12px", paddingTop: "10px" }}
              iconSize={isMobile ? 8 : 14}
            />
            <Area
              type="monotone"
              dataKey="delivered"
              name="Délivrés"
              stroke="#10B981"
              strokeWidth={2}
              fill="url(#colorSent)"
              dot={isMobile ? false : { fill: "#10B981", strokeWidth: 2, r: 3 }}
              activeDot={{ r: isMobile ? 4 : 6, fill: "#10B981" }}
            />
            <Area
              type="monotone"
              dataKey="sent"
              name="Envoyés"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#colorDelivered)"
              dot={isMobile ? false : { fill: "#3B82F6", strokeWidth: 2, r: 3 }}
              activeDot={{ r: isMobile ? 4 : 6, fill: "#3B82F6" }}
            />
            <Line
              type="monotone"
              dataKey="read"
              name="Lus"
              stroke="#8B5CF6"
              strokeWidth={2}
              dot={isMobile ? false : { fill: "#8B5CF6", strokeWidth: 2, r: 3 }}
              activeDot={{ r: isMobile ? 4 : 6 }}
            />
            <Line
              type="monotone"
              dataKey="failed"
              name="Échoués"
              stroke="#EF4444"
              strokeWidth={2}
              dot={isMobile ? false : { fill: "#EF4444", strokeWidth: 2, r: 3 }}
              activeDot={{ r: isMobile ? 4 : 6 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default LineChart;
