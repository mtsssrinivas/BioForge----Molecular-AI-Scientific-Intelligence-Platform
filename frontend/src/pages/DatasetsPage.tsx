import React from 'react';
import { StatusBadge } from '../components/common/StatusBadge';
import { Database, CheckCircle2, ArrowRight, UploadCloud } from 'lucide-react';

export const DatasetsPage: React.FC = () => {
  const steps = [
    { name: 'Upload', status: 'completed' },
    { name: 'Validate', status: 'completed' },
    { name: 'Clean', status: 'completed' },
    { name: 'Standardize', status: 'completed' },
    { name: 'Feature Gen', status: 'completed' },
    { name: 'Ready', status: 'completed' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            Molecular Datasets
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Curated, standardized molecular corpora with physicochemical descriptors and Morgan fingerprints.
          </p>
        </div>
        <button className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-md flex items-center space-x-1.5 shadow-xs transition-colors">
          <UploadCloud size={14} />
          <span>Upload Dataset</span>
        </button>
      </div>

      {/* Dataset Card */}
      <div className="bg-white border border-slate-200 rounded-md p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
              <Database size={20} />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-slate-900">Delaney ESOL (Aqueous Solubility)</h3>
                <StatusBadge status="Ready" />
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Benchmark dataset for estimating aqueous solubility (LogS in mol/L) from chemical structure.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono text-slate-400">Version: v1.2</span>
        </div>

        {/* Ingestion Workflow Indicator */}
        <div className="bg-slate-50 rounded-md p-3 border border-slate-200">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Ingestion & Standardization Pipeline
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {steps.map((step, idx) => (
              <React.Fragment key={step.name}>
                <div className="flex items-center space-x-1.5 bg-white px-2.5 py-1 rounded border border-slate-200 text-xs font-medium text-slate-700">
                  <CheckCircle2 size={13} className="text-emerald-600" />
                  <span>{step.name}</span>
                </div>
                {idx < steps.length - 1 && <ArrowRight size={12} className="text-slate-300" />}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Dataset Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs">
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <span className="text-slate-500 text-[11px]">Total Compounds</span>
            <p className="font-semibold text-slate-900 mt-0.5">50 molecules</p>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <span className="text-slate-500 text-[11px]">Task Type</span>
            <p className="font-semibold text-slate-900 mt-0.5">Regression (LogS)</p>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <span className="text-slate-500 text-[11px]">Features Computed</span>
            <p className="font-semibold text-slate-900 mt-0.5">RDKit 8 Descriptors + 1024-bit ECFP4</p>
          </div>
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <span className="text-slate-500 text-[11px]">Data Integrity</span>
            <p className="font-semibold text-emerald-700 mt-0.5">100% Valid • 0 Duplicates</p>
          </div>
        </div>
      </div>
    </div>
  );
};
