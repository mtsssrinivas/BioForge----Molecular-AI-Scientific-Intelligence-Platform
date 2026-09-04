import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Molecule } from '../types';
import { MoleculeModal } from '../components/molecules/MoleculeModal';
import { Search, Filter, Eye } from 'lucide-react';

export const MoleculesPage: React.FC = () => {
  const [molecules, setMolecules] = useState<Molecule[]>([]);
  const [selectedMolecule, setSelectedMolecule] = useState<Molecule | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMolecules() {
      try {
        const data = await api.getMolecules(50);
        setMolecules(data);
      } catch (err) {
        console.error('Failed to load molecules', err);
      } finally {
        setLoading(false);
      }
    }
    fetchMolecules();
  }, []);

  const filteredMolecules = molecules.filter((m) => {
    const s = searchTerm.toLowerCase();
    return (
      m.compound_id.toLowerCase().includes(s) ||
      m.canonical_smiles.toLowerCase().includes(s)
    );
  });

  const handleRowClick = async (mol: Molecule) => {
    try {
      const detail = await api.getMolecule(mol.id);
      setSelectedMolecule(detail);
    } catch {
      setSelectedMolecule(mol);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Filter and Search Bar */}
      <div className="bg-white p-4 rounded-md border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Compound ID or SMILES..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900"
          />
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-500">
          <Filter size={14} className="text-slate-400" />
          <span>Dataset:</span>
          <select className="bg-slate-50 border border-slate-200 text-slate-700 rounded px-2 py-1 text-xs focus:outline-none focus:border-emerald-500">
            <option value="all">Delaney ESOL (50 compounds)</option>
          </select>
        </div>
      </div>

      {/* High-density Scientific Data Table */}
      <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-4 py-2.5">Compound ID</th>
                <th className="px-4 py-2.5">Canonical SMILES</th>
                <th className="px-4 py-2.5">MW (g/mol)</th>
                <th className="px-4 py-2.5">LogP</th>
                <th className="px-4 py-2.5">TPSA (Å²)</th>
                <th className="px-4 py-2.5">HBD / HBA</th>
                <th className="px-4 py-2.5">Solubility (LogS)</th>
                <th className="px-4 py-2.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredMolecules.length > 0 ? (
                filteredMolecules.map((mol) => (
                  <tr
                    key={mol.id}
                    onClick={() => handleRowClick(mol)}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-2 font-mono font-medium text-slate-900">
                      {mol.compound_id}
                    </td>
                    <td className="px-4 py-2 font-mono text-[11px] text-slate-600 truncate max-w-[200px]" title={mol.canonical_smiles}>
                      {mol.canonical_smiles}
                    </td>
                    <td className="px-4 py-2">{mol.molecular_weight?.toFixed(2) || '—'}</td>
                    <td className="px-4 py-2 font-medium">{mol.logp?.toFixed(2) || '—'}</td>
                    <td className="px-4 py-2">{mol.tpsa?.toFixed(1) || '—'}</td>
                    <td className="px-4 py-2">
                      {mol.h_bond_donors ?? 0} / {mol.h_bond_acceptors ?? 0}
                    </td>
                    <td className="px-4 py-2 font-semibold text-emerald-700">
                      {mol.target_value !== undefined && mol.target_value !== null
                        ? mol.target_value.toFixed(2)
                        : '—'}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRowClick(mol);
                        }}
                        className="p-1 text-slate-400 hover:text-emerald-600 rounded hover:bg-slate-100"
                        title="View 2D Structure and Details"
                      >
                        <Eye size={14} />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                    {loading ? 'Loading molecular records from PostgreSQL/SQLite store...' : 'No matching molecules found.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2D Molecular Structure & Details Modal */}
      <MoleculeModal
        molecule={selectedMolecule}
        onClose={() => setSelectedMolecule(null)}
      />
    </div>
  );
};
