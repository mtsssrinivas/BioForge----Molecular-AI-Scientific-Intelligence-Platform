import React, { useState } from 'react';
import { api } from '../services/api';
import { Sparkles, CheckCircle2, Clock, Loader2, ArrowRight } from 'lucide-react';

export const PredictionPage: React.FC = () => {
  const [smiles, setSmiles] = useState('CC(=O)Oc1ccccc1C(=O)O'); // Aspirin
  const [modelType, setModelType] = useState('xgboost');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentJob, setCurrentJob] = useState<any>(null);
  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [progressStage, setProgressStage] = useState<string>('idle');
  const [progressPercent, setProgressPercent] = useState<number>(0);

  const samples = [
    { name: 'Aspirin', smiles: 'CC(=O)Oc1ccccc1C(=O)O' },
    { name: 'Ibuprofen', smiles: 'CC(C)Cc1ccc(cc1)C(C)C(=O)O' },
    { name: 'Caffeine', smiles: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C' },
    { name: 'Benzene', smiles: 'c1ccccc1' },
    { name: 'Ethanol', smiles: 'CCO' },
  ];

  const stagesList = [
    { id: 'preparing_data', label: 'Preparing Molecule' },
    { id: 'feature_generation', label: 'Feature Generation' },
    { id: 'model_inference', label: 'Neural Inference' },
    { id: 'persisting_results', label: 'Saving Results' },
    { id: 'completed', label: 'Completed' },
  ];

  const handleRunPrediction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!smiles.trim()) return;

    setIsSubmitting(true);
    setPredictionResult(null);
    setProgressStage('queued');
    setProgressPercent(10);

    try {
      // 1. Submit async job
      const job = await api.submitPredictionJob(smiles, modelType);
      setCurrentJob(job);

      // 2. Subscribe to Server-Sent Events (SSE)
      const eventSource = new EventSource(`/api/jobs/${job.job_id}/events`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.stage) {
            setProgressStage(data.stage);
            setProgressPercent(data.progress_percent || 50);
          }
        } catch {
          // heartbeat
        }
      };

      eventSource.addEventListener('done', async () => {
        eventSource.close();
        const updated = await api.getJob(job.job_id);
        setCurrentJob(updated);
        setPredictionResult(updated.result);
        setProgressStage('completed');
        setProgressPercent(100);
        setIsSubmitting(false);
      });

      eventSource.onerror = async () => {
        eventSource.close();
        const updated = await api.getJob(job.job_id);
        setCurrentJob(updated);
        if (updated.result) {
          setPredictionResult(updated.result);
          setProgressStage('completed');
          setProgressPercent(100);
        }
        setIsSubmitting(false);
      };
    } catch (err: any) {
      console.error('Job error', err);
      setIsSubmitting(false);
      setProgressStage('failed');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
          Molecular Property Prediction Workspace
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Execute classical XGBoost or PyTorch Graph Neural Network inference with real-time SSE progress telemetry.
        </p>
      </div>

      {/* Input Configuration Card */}
      <div className="bg-white border border-slate-200 rounded-md p-5 space-y-4">
        <form onSubmit={handleRunPrediction} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Molecular SMILES String
            </label>
            <input
              type="text"
              value={smiles}
              onChange={(e) => setSmiles(e.target.value)}
              placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O"
              className="w-full px-3 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900"
            />
          </div>

          {/* Preset Samples */}
          <div className="flex flex-wrap gap-1.5 items-center text-[11px] text-slate-500">
            <span className="font-semibold text-slate-400">Sample Compounds:</span>
            {samples.map((s) => (
              <button
                type="button"
                key={s.name}
                onClick={() => setSmiles(s.smiles)}
                className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition-colors font-medium"
              >
                {s.name}
              </button>
            ))}
          </div>

          {/* Model Selector */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Model Architecture
              </label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-emerald-500 text-slate-900"
              >
                <option value="xgboost">XGBoost Baseline (Descriptors + Morgan ECFP4)</option>
                <option value="gnn">PyTorch GNN (Message-Passing Graph Network)</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white rounded-md text-xs font-semibold shadow-xs transition-colors flex items-center justify-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    <span>Running Model Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={14} />
                    <span>Run Prediction</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Real-time SSE Stage Progress */}
      {progressStage !== 'idle' && (
        <div className="bg-white border border-slate-200 rounded-md p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Live Pipeline Stage Telemetry
            </h3>
            <span className="text-xs font-mono text-slate-500">
              Job ID: {currentJob?.job_id || 'Initializing...'}
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className="bg-emerald-600 h-2 transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Stage steps */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-1">
            {stagesList.map((stage) => {
              const isDone =
                progressPercent === 100 ||
                (stage.id === 'preparing_data' && progressPercent >= 20) ||
                (stage.id === 'feature_generation' && progressPercent >= 50) ||
                (stage.id === 'model_inference' && progressPercent >= 80) ||
                (stage.id === 'persisting_results' && progressPercent >= 95);

              const isCurrent = progressStage === stage.id;

              return (
                <div
                  key={stage.id}
                  className={`p-2.5 rounded border text-xs flex items-center space-x-1.5 transition-colors ${
                    isDone
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-800 font-semibold'
                      : isCurrent
                      ? 'bg-blue-50 border-blue-200 text-blue-800 font-semibold'
                      : 'bg-slate-50 border-slate-200 text-slate-400'
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 size={13} className="text-emerald-600 shrink-0" />
                  ) : isCurrent ? (
                    <Loader2 size={13} className="animate-spin text-blue-600 shrink-0" />
                  ) : (
                    <Clock size={13} className="shrink-0" />
                  )}
                  <span className="truncate">{stage.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Prediction Output Card */}
      {predictionResult && (
        <div className="bg-white border border-slate-200 rounded-md p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900">Prediction Results</h3>
            <span className="text-xs font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
              Status: Valid Prediction
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 bg-slate-50 rounded border border-slate-200">
              <span className="text-xs text-slate-500">Predicted Aqueous Solubility (LogS)</span>
              <p className="text-2xl font-bold text-emerald-700 mt-1">
                {predictionResult.predicted_value} {predictionResult.unit}
              </p>
            </div>

            <div className="p-4 bg-slate-50 rounded border border-slate-200">
              <span className="text-xs text-slate-500">Evaluated Model</span>
              <p className="text-sm font-bold text-slate-900 uppercase mt-1">
                {predictionResult.model_type || modelType}
              </p>
            </div>

            <div className="p-4 bg-slate-50 rounded border border-slate-200">
              <span className="text-xs text-slate-500">Canonical SMILES</span>
              <p className="text-xs font-mono text-slate-800 truncate mt-1">
                {predictionResult.canonical_smiles || smiles}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
