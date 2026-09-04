import React from 'react';
import { Settings, Server, Database, Key } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
          Node Settings & Architecture
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Production environment variables, local database connections, and model serving configurations.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-5 space-y-4">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
          <Server size={14} className="text-emerald-600" />
          <span>Core Service Configuration</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <span className="text-slate-500 text-[11px]">API Host / Port</span>
            <p className="font-mono text-slate-800 mt-0.5">http://0.0.0.0:8000</p>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <span className="text-slate-500 text-[11px]">Database Dialect</span>
            <p className="font-mono text-slate-800 mt-0.5">PostgreSQL 16 + pgvector (SQLite dev fallback)</p>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <span className="text-slate-500 text-[11px]">Asynchronous Queue</span>
            <p className="font-mono text-slate-800 mt-0.5">Celery Distributed Worker (Redis Broker: 6379)</p>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <span className="text-slate-500 text-[11px]">Vector Embeddings</span>
            <p className="font-mono text-slate-800 mt-0.5">Local Deterministic 384-Dim (all-MiniLM-L6-v2 spec)</p>
          </div>
        </div>
      </div>
    </div>
  );
};
