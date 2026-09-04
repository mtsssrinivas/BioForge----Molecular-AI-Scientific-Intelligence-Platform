export interface Molecule {
  id: string;
  compound_id: string;
  dataset_id: string;
  canonical_smiles: string;
  original_smiles: string;
  target_value?: number;
  molecular_weight?: number;
  logp?: number;
  tpsa?: number;
  h_bond_donors?: number;
  h_bond_acceptors?: number;
  rotatable_bonds?: number;
  svg_2d?: string;
  fingerprint_bits?: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string;
  total_records: number;
  task_type: string;
  target_property: string;
  created_at: string;
}

export interface MLModel {
  id: string;
  name: string;
  model_type: string;
  framework: string;
  version: string;
  is_active: boolean;
}

export interface Experiment {
  id: string;
  name: string;
  model_id: string;
  dataset_id?: string;
  status: string;
  metrics_val?: Record<string, number>;
  metrics_test?: {
    rmse?: number;
    mae?: number;
    r2?: number;
    [key: string]: any;
  };
  hyperparameters?: Record<string, any>;
  feature_config?: Record<string, any>;
  feature_importance?: Record<string, number>;
  training_duration_seconds: number;
  created_at?: string;
}

export interface ModelComparison {
  dataset_name: string;
  dataset_hash: string;
  split_identical: boolean;
  models: {
    xgboost: {
      experiment_id: string;
      model_type: string;
      metrics_test: { rmse: number; mae: number; r2: number };
      training_duration_seconds: number;
      artifact: string;
    };
    gnn: {
      experiment_id: string;
      model_type: string;
      metrics_test: { rmse: number; mae: number; r2: number };
      training_duration_seconds: number;
      artifact: string;
    };
  };
  summary: {
    lower_test_rmse_winner: string;
    higher_test_r2_winner: string;
    rmse_difference: number;
    r2_difference: number;
  };
}

export interface LiteratureChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  title: string;
  authors: string;
  source: string;
  publication_year: number;
  content: string;
  citation_reference: string;
  relevance_score?: number;
}

export interface ScientificRAGResponse {
  question: string;
  answer: string;
  confidence: number;
  evidence: LiteratureChunk[];
  citations: string[];
  limitations: string;
  molecular_context?: {
    smiles?: string;
    canonical_smiles?: string;
    predicted_value?: number;
    unit?: string;
    model_id?: string;
    descriptors?: Record<string, number>;
  };
}

export interface Job {
  job_id: string;
  job_type: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  current_stage: string;
  progress_percent: number;
  result?: any;
  error?: string;
  created_at: string;
  completed_at?: string;
}
