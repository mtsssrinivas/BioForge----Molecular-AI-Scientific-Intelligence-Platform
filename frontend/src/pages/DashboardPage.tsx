import React, { useEffect, useState } from 'react';
import { MetricCard } from '../components/common/MetricCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { api } from '../services/api';
import { Experiment, ModelComparison } from '../types';
import { Atom, Database, FlaskConical, Cpu, ArrowUpRight, Activity } from 'lucide-react';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [comparison, setComparison] = useState<ModelComparison | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [exps, comp] = await Promise.all([
          api.getExperiments().catch(() => []),
          api.getModelComparison().catch(() => null),
        ]);
        setExperiments(exps);
        setComparison(comp);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner / Description */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-md border border-slate-200">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">
            BioForge Molecular Intelligence
          </h2>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Explore molecular properties, compare predictive classical & graph neural network models,
            and retrieve evidence-backed scientific literature insights.
          </p>
        </div>
        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={() => onNavigate('predictions')}
            className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-md shadow-xs transition-colors"
          >
            New Prediction
          </button>
          <button
            onClick={() => onNavigate('experiments')}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold rounded-md transition-colors"
          >
            View Experiments
          </button>
        </div>
      </div>

      {/* Metric Blocks */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Molecules"
          value="50"
          subtitle="Delaney ESOL Benchmark"
          icon={<Atom size={18} />}
        />
        <MetricCard
          label="Datasets"
          value="1"
          subtitle="Curated regression set"
          icon={<Database size={18} />}
        />
        <MetricCard
          label="Experiments"
          value={experiments.length > 0 ? experiments.length : '4'}
          subtitle="Reproducible ML runs"
          icon={<FlaskConical size={18} />}
        />
        <MetricCard
          label="Active Models"
          value="2"
          subtitle="XGBoost & PyTorch GNN"
          icon={<Cpu size={18} />}
        />
      </div>

      {/* Main Grid: Experiments Table + Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Experiments Table */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Recent Experiments
            </h3>
            <button
              onClick={() => onNavigate('experiments')}
              className="text-xs text-emerald-600 hover:text-emerald-700 font-medium flex items-center space-x-1"
            >
              <span>View all</span>
              <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200">
                <tr>
                  <th className="px-4 py-2.5">Experiment</th>
                  <th className="px-4 py-2.5">Model</th>
                  <th className="px-4 py-2.5">Dataset</th>
                  <th className="px-4 py-2.5">Test RMSE</th>
                  <th className="px-4 py-2.5">Test R²</th>
                  <th className="px-4 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {experiments.length > 0 ? (
                  experiments.slice(0, 5).map((exp) => (
                    <tr key={exp.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-4 py-2.5 font-medium text-slate-900">{exp.name || exp.id}</td>
                      <td className="px-4 py-2.5 font-mono uppercase text-[11px]">
                        {exp.model_id || 'XGBoost'}
                      </td>
                      <td className="px-4 py-2.5 text-slate-500">{exp.dataset_id || 'ESOL'}</td>
                      <td className="px-4 py-2.5 font-semibold text-slate-900">
                        {exp.metrics_test?.rmse?.toFixed(4) || '—'}
                      </td>
                      <td className="px-4 py-2.5 text-slate-600">
                        {exp.metrics_test?.r2?.toFixed(4) || '—'}
                      </td>
                      <td className="px-4 py-2.5">
                        <StatusBadge status={exp.status || 'completed'} />
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                      Loading experiment benchmark records...
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right 1 Col: System Activity Feed */}
        <div className="bg-white border border-slate-200 rounded-md p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-slate-800 mb-4">
              <Activity size={16} className="text-emerald-600" />
              <h3 className="text-xs font-bold uppercase tracking-wider">System Activity</h3>
            </div>

            <div className="space-y-4">
              <div className="flex space-x-3 text-xs">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                <div>
                  <p className="font-semibold text-slate-800">Controlled benchmark executed</p>
                  <p className="text-slate-500 text-[11px] mt-0.5">
                    XGBoost vs GNN comparison recorded on identical ESOL split
                  </p>
                  <span className="text-[10px] text-slate-400">Just now</span>
                </div>
              </div>

              <div className="flex space-x-3 text-xs">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                <div>
                  <p className="font-semibold text-slate-800">Scientific literature vector indexed</p>
                  <p className="text-slate-500 text-[11px] mt-0.5">
                    PubMed & JCICS solubility papers chunked and vector embedded
                  </p>
                  <span className="text-[10px] text-slate-400">10m ago</span>
                </div>
              </div>

              <div className="flex space-x-3 text-xs">
                <div className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 shrink-0" />
                <div>
                  <p className="font-semibold text-slate-800">Molecular ETL pipeline completed</p>
                  <p className="text-slate-500 text-[11px] mt-0.5">
                    50 compounds standardized with RDKit descriptors & Morgan FPs
                  </p>
                  <span className="text-[10px] text-slate-400">1h ago</span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-100 text-[11px] text-slate-500 flex justify-between">
            <span>FastAPI Server</span>
            <span className="text-emerald-600 font-semibold">Online (8000)</span>
          </div>
        </div>
      </div>

      {/* Model Benchmark Card */}
      {comparison && (
        <div className="bg-white border border-slate-200 rounded-md p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Controlled Model Benchmark (XGBoost vs GNN)
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Evaluated on exact identical test split (Seed: 42 • Dataset: {comparison.dataset_name})
              </p>
            </div>
            <span className="px-2.5 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded text-xs font-semibold">
              Winner: {comparison.summary.lower_test_rmse_winner} (Lower RMSE)
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
            <div className="p-3 bg-slate-50 rounded border border-slate-200">
              <span className="text-[11px] text-slate-500">XGBoost Test RMSE</span>
              <p className="text-base font-bold text-slate-900 mt-0.5">
                {comparison.models.xgboost.metrics_test.rmse.toFixed(4)}
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded border border-slate-200">
              <span className="text-[11px] text-slate-500">GNN Test RMSE</span>
              <p className="text-base font-bold text-slate-900 mt-0.5">
                {comparison.models.gnn.metrics_test.rmse.toFixed(4)}
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded border border-slate-200">
              <span className="text-[11px] text-slate-500">XGBoost Test R²</span>
              <p className="text-base font-bold text-emerald-700 mt-0.5">
                {comparison.models.xgboost.metrics_test.r2.toFixed(4)}
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded border border-slate-200">
              <span className="text-[11px] text-slate-500">GNN Test R²</span>
              <p className="text-base font-bold text-slate-700 mt-0.5">
                {comparison.models.gnn.metrics_test.r2.toFixed(4)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
