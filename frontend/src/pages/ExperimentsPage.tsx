import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Experiment } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { FlaskConical, Clock, BarChart3 } from 'lucide-react';

export const ExperimentsPage: React.FC = () => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedExp, setSelectedExp] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchExps() {
      try {
        const data = await api.getExperiments();
        setExperiments(data);
        if (data.length > 0) {
          setSelectedExp(data[0]);
        }
      } catch (err) {
        console.error('Failed to load experiments', err);
      } finally {
        setLoading(false);
      }
    }
    fetchExps();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            ML Experiments & Evaluation
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit reproducible classical ML and graph neural network property prediction benchmarks.
          </p>
        </div>
      </div>

      {/* Main Grid: Experiments List + Workspace Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Experiments List */}
        <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 font-bold text-xs text-slate-800 uppercase tracking-wider">
            Experiment Runs
          </div>
          <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
            {experiments.map((exp) => {
              const isSelected = selectedExp?.id === exp.id;
              return (
                <div
                  key={exp.id}
                  onClick={() => setSelectedExp(exp)}
                  className={`p-4 cursor-pointer transition-colors ${
                    isSelected ? 'bg-emerald-50/70 border-l-3 border-emerald-600' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-slate-900">{exp.name || exp.id}</span>
                    <StatusBadge status={exp.status || 'completed'} />
                  </div>
                  <div className="flex items-center space-x-3 text-[11px] text-slate-500 mt-2">
                    <span className="font-mono uppercase">{exp.model_id}</span>
                    <span>•</span>
                    <span>Test RMSE: {exp.metrics_test?.rmse?.toFixed(4) || '—'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Detailed Experiment Workspace */}
        <div className="lg:col-span-2 space-y-4">
          {selectedExp ? (
            <div className="bg-white border border-slate-200 rounded-md p-5 space-y-5">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <FlaskConical size={18} className="text-emerald-600" />
                    <h3 className="text-base font-bold text-slate-900">{selectedExp.name || selectedExp.id}</h3>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">ID: {selectedExp.id}</p>
                </div>
                <div className="flex items-center space-x-2 text-xs text-slate-500">
                  <Clock size={14} />
                  <span>Duration: {selectedExp.training_duration_seconds}s</span>
                </div>
              </div>

              {/* Metric Blocks */}
              <div>
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Test Evaluation Metrics
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-50 rounded border border-slate-200 text-center">
                    <span className="text-[11px] text-slate-500">Test RMSE</span>
                    <p className="text-xl font-bold text-slate-900 mt-0.5">
                      {selectedExp.metrics_test?.rmse?.toFixed(4) || '—'}
                    </p>
                  </div>

                  <div className="p-3 bg-slate-50 rounded border border-slate-200 text-center">
                    <span className="text-[11px] text-slate-500">Test MAE</span>
                    <p className="text-xl font-bold text-slate-900 mt-0.5">
                      {selectedExp.metrics_test?.mae?.toFixed(4) || '—'}
                    </p>
                  </div>

                  <div className="p-3 bg-slate-50 rounded border border-slate-200 text-center">
                    <span className="text-[11px] text-slate-500">Test R² Score</span>
                    <p className="text-xl font-bold text-emerald-700 mt-0.5">
                      {selectedExp.metrics_test?.r2?.toFixed(4) || '—'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Feature Importance or Loss Info */}
              {selectedExp.feature_importance && (
                <div>
                  <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    <BarChart3 size={14} />
                    <span>Top Feature Importance</span>
                  </div>
                  <div className="space-y-1.5 bg-slate-50 p-3 rounded border border-slate-200">
                    {Object.entries(selectedExp.feature_importance).slice(0, 5).map(([feat, val]) => (
                      <div key={feat} className="flex items-center justify-between text-xs">
                        <span className="font-mono text-slate-700">{feat}</span>
                        <span className="font-semibold text-slate-900">{(val as number).toFixed(4)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Configuration Details */}
              <div className="grid grid-cols-2 gap-3 text-xs pt-2 border-t border-slate-100">
                <div>
                  <span className="text-slate-500 font-medium">Dataset Partition</span>
                  <p className="text-slate-800 font-mono mt-0.5">Train: 80% • Val: 10% • Test: 10%</p>
                </div>
                <div>
                  <span className="text-slate-500 font-medium">Split Random Seed</span>
                  <p className="text-slate-800 font-mono mt-0.5">Seed 42 (Reproducible)</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-md p-8 text-center text-slate-400 text-xs">
              Select an experiment to inspect parameters and performance.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
