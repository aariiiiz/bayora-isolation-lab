import React from "react";
import { cn } from "../../lib/utils";
import { RiskLevel } from "../../types";

interface RiskMeterProps {
  score: number;
  level: RiskLevel;
  size?: "sm" | "md" | "lg";
}

export const RiskMeter: React.FC<RiskMeterProps> = ({ score, level, size = "md" }) => {
  const getColor = () => {
    switch (level) {
      case "CRITICAL":
        return "bg-rose-500 text-rose-700 border-rose-300";
      case "HIGH":
        return "bg-orange-500 text-orange-700 border-orange-300";
      case "MEDIUM":
        return "bg-amber-500 text-amber-700 border-amber-300";
      case "LOW":
        return "bg-blue-500 text-blue-700 border-blue-300";
      case "CLEAN":
      default:
        return "bg-emerald-500 text-emerald-700 border-emerald-300";
    }
  };

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-slate-600">Risk Assessment</span>
        <span className="font-bold text-slate-800 font-heading">
          {score.toFixed(0)} <span className="text-slate-400 font-normal">/ 100</span> ({level})
        </span>
      </div>
      <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden p-0.5 border border-slate-200">
        <div
          className={cn("h-full rounded-full transition-all duration-500", getColor().split(" ")[0])}
          style={{ width: `${Math.max(4, Math.min(100, score))}%` }}
        />
      </div>
    </div>
  );
};
