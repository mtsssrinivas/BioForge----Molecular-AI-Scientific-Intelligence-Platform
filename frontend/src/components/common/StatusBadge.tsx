import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const s = status.toLowerCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-200';
  if (s === 'completed' || s === 'active' || s === 'ready') {
    styles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (s === 'running' || s === 'training') {
    styles = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (s === 'queued') {
    styles = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (s === 'failed' || s === 'error') {
    styles = 'bg-rose-50 text-rose-700 border-rose-200';
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${styles} capitalize`}
    >
      {status}
    </span>
  );
};
