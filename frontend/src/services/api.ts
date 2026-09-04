import {
  Molecule,
  MLModel,
  Experiment,
  ModelComparison,
  LiteratureChunk,
  ScientificRAGResponse,
  Job,
} from '../types';

const API_BASE = '/api';

export const api = {
  // Molecules
  getMolecules: async (limit = 50, skip = 0): Promise<Molecule[]> => {
    const res = await fetch(`${API_BASE}/molecules?limit=${limit}&skip=${skip}`);
    if (!res.ok) throw new Error('Failed to fetch molecules');
    return res.json();
  },

  getMolecule: async (id: string): Promise<Molecule> => {
    const res = await fetch(`${API_BASE}/molecules/${id}`);
    if (!res.ok) throw new Error('Failed to fetch molecule details');
    return res.json();
  },

  // Predictions
  predictSmiles: async (smiles: string, modelId = 'xgboost_esol_latest') => {
    const res = await fetch(`${API_BASE}/predictions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ smiles, model_id: modelId }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Prediction failed');
    }
    return res.json();
  },

  // Models
  getModels: async (): Promise<MLModel[]> => {
    const res = await fetch(`${API_BASE}/models`);
    if (!res.ok) throw new Error('Failed to fetch models');
    return res.json();
  },

  // Experiments
  getExperiments: async (): Promise<Experiment[]> => {
    const res = await fetch(`${API_BASE}/experiments`);
    if (!res.ok) throw new Error('Failed to fetch experiments');
    return res.json();
  },

  getModelComparison: async (): Promise<ModelComparison> => {
    const res = await fetch(`${API_BASE}/experiments/comparison/latest`);
    if (!res.ok) throw new Error('Failed to fetch model comparison');
    return res.json();
  },

  // Literature & RAG
  searchLiterature: async (query: string, topK = 5, sourceFilter?: string) => {
    const res = await fetch(`${API_BASE}/literature/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        top_k: topK,
        source_filter: sourceFilter || null,
      }),
    });
    if (!res.ok) throw new Error('Literature search failed');
    return res.json();
  },

  queryRAG: async (
    question: string,
    smiles?: string,
    topK = 3
  ): Promise<ScientificRAGResponse> => {
    const res = await fetch(`${API_BASE}/rag/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        smiles: smiles || null,
        top_k: topK,
      }),
    });
    if (!res.ok) throw new Error('RAG query failed');
    return res.json();
  },

  // Jobs
  submitPredictionJob: async (smiles: string, modelType = 'xgboost'): Promise<Job> => {
    const res = await fetch(
      `${API_BASE}/jobs/prediction?smiles=${encodeURIComponent(smiles)}&model_type=${modelType}`,
      { method: 'POST' }
    );
    if (!res.ok) throw new Error('Failed to submit prediction job');
    return res.json();
  },

  getJobs: async (): Promise<Job[]> => {
    const res = await fetch(`${API_BASE}/jobs`);
    if (!res.ok) throw new Error('Failed to fetch jobs');
    return res.json();
  },

  getJob: async (jobId: string): Promise<Job> => {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) throw new Error('Failed to fetch job');
    return res.json();
  },
};
