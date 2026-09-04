import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtitle,
  trend,
  icon,
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-4 shadow-xs flex flex-col justify-between">
      <div className="flex items-center justify-between text-slate-500 mb-1">
        <span className="text-xs font-semibold uppercase tracking-wider">{label}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <div className="flex items-baseline space-x-2">
        <span className="text-2xl font-bold text-slate-900 tracking-tight">{value}</span>
        {trend && <span className="text-xs font-medium text-emerald-600">{trend}</span>}
      </div>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  );
};
