import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Job } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { RefreshCw, ListTodo } from 'lucide-react';

export const JobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const data = await api.getJobs();
      setJobs(data);
    } catch (err) {
      console.error('Failed to load jobs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            System Job Telemetry
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Monitor asynchronous molecular inference tasks, Celery worker executions, and SSE event dispatchers.
          </p>
        </div>

        <button
          onClick={fetchJobs}
          disabled={loading}
          className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-md flex items-center space-x-1.5 shadow-xs transition-colors"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Jobs Table */}
      <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-4 py-2.5">Job ID</th>
                <th className="px-4 py-2.5">Type</th>
                <th className="px-4 py-2.5">Current Stage</th>
                <th className="px-4 py-2.5">Progress</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {jobs.length > 0 ? (
                jobs.map((j) => (
                  <tr key={j.job_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-2.5 font-mono font-medium text-slate-900">
                      {j.job_id}
                    </td>
                    <td className="px-4 py-2.5 capitalize">{j.job_type}</td>
                    <td className="px-4 py-2.5 font-mono text-[11px] text-slate-600">
                      {j.current_stage}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-emerald-600 h-1.5"
                            style={{ width: `${j.progress_percent}%` }}
                          />
                        </div>
                        <span className="text-[11px] font-mono text-slate-500">
                          {j.progress_percent}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5">
                      <StatusBadge status={j.status} />
                    </td>
                    <td className="px-4 py-2.5 text-slate-400 text-[11px]">
                      {new Date(j.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    No active or recent jobs found. Run a prediction to initiate an async pipeline.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
