import React from 'react';
import { Molecule } from '../../types';
import { X, ExternalLink } from 'lucide-react';

interface MoleculeModalProps {
  molecule: Molecule | null;
  onClose: () => void;
}

export const MoleculeModal: React.FC<MoleculeModalProps> = ({ molecule, onClose }) => {
  if (!molecule) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-xl max-w-2xl w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50/50">
          <div>
            <h3 className="text-base font-semibold text-slate-900">{molecule.compound_id}</h3>
            <p className="text-xs text-slate-500 font-mono mt-0.5">{molecule.canonical_smiles}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md hover:bg-slate-100 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* 2D Structure Rendering */}
          <div className="flex flex-col items-center justify-center border border-slate-200 rounded-md p-4 bg-white min-h-[220px]">
            {molecule.svg_2d ? (
              <div
                className="w-full max-w-[320px] max-h-[200px] flex items-center justify-center"
                dangerouslySetInnerHTML={{ __html: molecule.svg_2d }}
              />
            ) : (
              <div className="text-xs text-slate-400 font-mono">Structure rendering generated via RDKit</div>
            )}
          </div>

          {/* Physicochemical Descriptors Grid */}
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Physicochemical Properties
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-xs text-slate-500">Molecular Weight</span>
                <p className="text-sm font-semibold text-slate-900 mt-0.5">
                  {molecule.molecular_weight ? molecule.molecular_weight.toFixed(2) : '—'} g/mol
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-xs text-slate-500">LogP (Partition Coeff)</span>
                <p className="text-sm font-semibold text-slate-900 mt-0.5">
                  {molecule.logp ? molecule.logp.toFixed(2) : '—'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-xs text-slate-500">TPSA (Polar Surface Area)</span>
                <p className="text-sm font-semibold text-slate-900 mt-0.5">
                  {molecule.tpsa ? molecule.tpsa.toFixed(1) : '—'} Å²
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-xs text-slate-500">H-Bond Donors</span>
                <p className="text-sm font-semibold text-slate-900 mt-0.5">
                  {molecule.h_bond_donors ?? '—'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-xs text-slate-500">H-Bond Acceptors</span>
                <p className="text-sm font-semibold text-slate-900 mt-0.5">
                  {molecule.h_bond_acceptors ?? '—'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-xs text-slate-500">Measured Solubility (LogS)</span>
                <p className="text-sm font-semibold text-emerald-700 mt-0.5">
                  {molecule.target_value !== undefined && molecule.target_value !== null
                    ? `${molecule.target_value.toFixed(2)} log mol/L`
                    : '—'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end px-6 py-3 border-t border-slate-200 bg-slate-50/50">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 bg-white border border-slate-300 text-slate-700 rounded text-xs font-medium hover:bg-slate-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
