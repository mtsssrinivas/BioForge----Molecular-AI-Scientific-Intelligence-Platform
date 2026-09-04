import React, { useState } from 'react';
import { api } from '../services/api';
import { ScientificRAGResponse } from '../types';
import { Brain, ShieldAlert, Sparkles, BookOpen, Quote, Info } from 'lucide-react';

export const RAGPage: React.FC = () => {
  const [question, setQuestion] = useState(
    'How do molecular weight and LogP govern aqueous solubility according to Delaney ESOL?'
  );
  const [smiles, setSmiles] = useState('CC(=O)Oc1ccccc1C(=O)O'); // Aspirin
  const [response, setResponse] = useState<ScientificRAGResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    try {
      const res = await api.queryRAG(question, smiles || undefined, 3);
      setResponse(res);
    } catch (err) {
      console.error('RAG query failed', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
          Evidence-Grounded Scientific Intelligence
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Non-generative hallucination-controlled synthesis strictly citing retrieved literature and empirical model predictions.
        </p>
      </div>

      {/* Query Form Workspace */}
      <div className="bg-white border border-slate-200 rounded-md p-5 space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Scientific Question / Hypothesis
            </label>
            <textarea
              rows={2}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Formulate an inquiry (e.g. How do aromatic bonds influence solubility?)"
              className="w-full p-2.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900 leading-relaxed"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Optional Molecular Context (SMILES)
              </label>
              <input
                type="text"
                value={smiles}
                onChange={(e) => setSmiles(e.target.value)}
                placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O"
                className="w-full px-3 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900"
              />
            </div>

            <div className="flex items-end space-x-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold shadow-xs transition-colors"
              >
                {loading ? 'Synthesizing with Literature...' : 'Run Evidence Analysis'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Structured Scientific Analysis Output */}
      {response && (
        <div className="bg-white border border-slate-200 rounded-md p-6 space-y-6">
          {/* Header Metadata */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Brain size={18} className="text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">Scientific Synthesis Report</h3>
            </div>
            <div className="flex items-center space-x-3 text-xs">
              <span className="text-slate-500">
                Confidence: <strong className="text-emerald-700">{Math.round(response.confidence * 100)}%</strong>
              </span>
              <span>•</span>
              <span className="text-slate-500">
                Citations: <strong>{response.citations.length}</strong>
              </span>
            </div>
          </div>

          {/* Synthesized Answer */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Validated Findings
            </h4>
            <div className="p-4 bg-slate-50/80 rounded-md border border-slate-200 text-xs text-slate-800 leading-relaxed font-sans whitespace-pre-line">
              {response.answer}
            </div>
          </div>

          {/* Molecular Prediction Notice if present */}
          {response.molecular_context && response.molecular_context.predicted_value !== undefined && (
            <div className="p-4 bg-emerald-50/60 rounded-md border border-emerald-200 flex items-start space-x-3 text-xs">
              <Sparkles size={16} className="text-emerald-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-emerald-900">Model Prediction Integration</span>
                <p className="text-emerald-800 text-[11px] mt-0.5">
                  Predicted aqueous solubility: <strong>{response.molecular_context.predicted_value} {response.molecular_context.unit}</strong> via model <em>{response.molecular_context.model_id}</em>.
                </p>
              </div>
            </div>
          )}

          {/* Retrieved Evidence Source Records */}
          <div>
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
              Retrieved Peer-Reviewed Evidence
            </h4>
            <div className="space-y-2">
              {response.evidence.map((item) => (
                <div key={item.id} className="p-3 bg-white rounded border border-slate-200 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-900">{item.title}</span>
                    <span className="px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded font-mono text-[10px] font-bold">
                      {item.citation_reference}
                    </span>
                  </div>
                  <p className="text-slate-600 text-[11px] font-serif italic">"{item.content}"</p>
                  <div className="text-[10px] text-slate-400 mt-1">
                    {item.authors} • {item.source} ({item.publication_year})
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Limitations and Guardrails */}
          <div className="p-3 bg-slate-50 rounded border border-slate-200 flex items-start space-x-2 text-[11px] text-slate-600">
            <Info size={14} className="text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-700">Scientific Limitations:</span>{' '}
              {response.limitations}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
