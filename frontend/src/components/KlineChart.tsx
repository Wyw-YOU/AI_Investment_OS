"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import type { StockHistory } from "@/lib/types";

interface Props {
  data: StockHistory[];
  indicators?: { ma5?: number[]; ma10?: number[]; ma20?: number[]; macd?: { dif_list: number[]; dea_list: number[]; macd_list: number[] } };
}

export default function KlineChart({ data, indicators }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || !data.length) return;

    const chart = echarts.init(chartRef.current, "dark");
    const dates = data.map((d) => d.date);
    const ohlc = data.map((d) => [d.open, d.close, d.low, d.high]);
    const volumes = data.map((d) => d.volume);

    const option: echarts.EChartsOption = {
      backgroundColor: "transparent",
      tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
      grid: [
        { left: "8%", right: "3%", top: "5%", height: "55%" },
        { left: "8%", right: "3%", top: "65%", height: "12%" },
        { left: "8%", right: "3%", top: "82%", height: "12%" },
      ],
      xAxis: [
        { type: "category", data: dates, gridIndex: 0, axisLabel: { show: false } },
        { type: "category", data: dates, gridIndex: 1, axisLabel: { show: false } },
        { type: "category", data: dates, gridIndex: 2, axisLabel: { show: true, fontSize: 10 } },
      ],
      yAxis: [
        { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: "#334155" } } },
        { scale: true, gridIndex: 1, splitLine: { show: false } },
        { scale: true, gridIndex: 2, splitLine: { show: false } },
      ],
      series: [
        {
          type: "candlestick",
          data: ohlc,
          xAxisIndex: 0,
          yAxisIndex: 0,
          itemStyle: { color: "#ef4444", color0: "#22c55e", borderColor: "#ef4444", borderColor0: "#22c55e" },
        },
        {
          type: "bar",
          data: volumes,
          xAxisIndex: 1,
          yAxisIndex: 1,
          itemStyle: {
            color: (params: { dataIndex: number }) => {
              const d = data[params.dataIndex];
              return d && d.close >= d.open ? "#ef444480" : "#22c55e80";
            },
          },
        },
        // MACD
        ...(indicators?.macd
          ? [
              { type: "line" as const, data: indicators.macd.dif_list, xAxisIndex: 2, yAxisIndex: 2, lineStyle: { width: 1 }, name: "DIF" },
              { type: "line" as const, data: indicators.macd.dea_list, xAxisIndex: 2, yAxisIndex: 2, lineStyle: { width: 1 }, name: "DEA" },
            ]
          : []),
        // MA lines
        ...(indicators?.ma5
          ? [{ type: "line" as const, data: indicators.ma5, xAxisIndex: 0, yAxisIndex: 0, lineStyle: { width: 1, color: "#facc15" }, name: "MA5", symbol: "none" }]
          : []),
        ...(indicators?.ma10
          ? [{ type: "line" as const, data: indicators.ma10, xAxisIndex: 0, yAxisIndex: 0, lineStyle: { width: 1, color: "#06b6d4" }, name: "MA10", symbol: "none" }]
          : []),
        ...(indicators?.ma20
          ? [{ type: "line" as const, data: indicators.ma20, xAxisIndex: 0, yAxisIndex: 0, lineStyle: { width: 1, color: "#a855f7" }, name: "MA20", symbol: "none" }]
          : []),
      ],
    };

    chart.setOption(option);
    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [data, indicators]);

  return <div ref={chartRef} className="w-full h-[500px]" />;
}
