import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { MLModel } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { Cpu, Layers, HardDrive } from 'lucide-react';

export const ModelsPage: React.FC = () => {
  const [models, setModels] = useState<MLModel[]>([]);

  useEffect(() => {
    async function loadModels() {
      try {
        const data = await api.getModels();
        setModels(data);
      } catch (err) {
        console.error('Failed to load models', err);
      }
    }
    loadModels();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
          Model Registry
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Audited machine learning and graph neural network checkpoints available for inference.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {models.map((model) => (
          <div
            key={model.id}
            className="bg-white border border-slate-200 rounded-md p-5 space-y-4 hover:border-slate-300 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-slate-100 text-slate-700 rounded border border-slate-200">
                  <Cpu size={20} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{model.name}</h3>
                  <span className="text-xs text-slate-400 font-mono">{model.id}</span>
                </div>
              </div>
              <StatusBadge status={model.is_active ? 'Active' : 'Archived'} />
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded border border-slate-200">
              <div>
                <span className="text-slate-500 text-[11px]">Architecture</span>
                <p className="font-semibold text-slate-900 capitalize mt-0.5">{model.model_type}</p>
              </div>
              <div>
                <span className="text-slate-500 text-[11px]">Framework</span>
                <p className="font-semibold text-slate-900 mt-0.5">{model.framework}</p>
              </div>
              <div>
                <span className="text-slate-500 text-[11px]">Artifact Format</span>
                <p className="font-semibold text-slate-900 mt-0.5">
                  {model.model_type === 'gnn' ? 'PyTorch State Dict (.pt)' : 'JSON Booster (.json)'}
                </p>
              </div>
              <div>
                <span className="text-slate-500 text-[11px]">Version</span>
                <p className="font-semibold text-slate-900 mt-0.5">{model.version}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
