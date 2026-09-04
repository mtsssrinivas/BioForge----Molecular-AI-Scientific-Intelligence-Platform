import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LiteratureChunk } from '../types';
import { Search, BookOpen, ExternalLink, BookmarkCheck } from 'lucide-react';

export const LiteraturePage: React.FC = () => {
  const [query, setQuery] = useState('aqueous solubility Delaney LogP molecular weight');
  const [results, setResults] = useState<LiteratureChunk[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (q = query) => {
    setLoading(true);
    try {
      const res = await api.searchLiterature(q, 5);
      setResults(res.evidence || []);
    } catch (err) {
      console.error('Literature search failed', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
          Scientific Literature & Vector Evidence Store
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Semantic literature search across indexed peer-reviewed publications using 384-dimensional vector embeddings.
        </p>
      </div>

      {/* Search Input Bar */}
      <div className="bg-white p-4 rounded-md border border-slate-200">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search scientific literature (e.g. Delaney solubility, GNN molecular property)..."
              className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900"
            />
          </div>
          <button
            onClick={() => handleSearch()}
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold shadow-xs transition-colors shrink-0"
          >
            {loading ? 'Searching...' : 'Search Literature'}
          </button>
        </div>

        {/* Preset Query Chips */}
        <div className="flex flex-wrap gap-1.5 mt-3 text-[11px] text-slate-500 items-center">
          <span className="font-semibold text-slate-400">Suggested:</span>
          {['Delaney ESOL aqueous solubility', 'Message Passing Neural Networks MPNN', 'Lipinski rule of five permeability'].map(
            (tag) => (
              <button
                key={tag}
                onClick={() => {
                  setQuery(tag);
                  handleSearch(tag);
                }}
                className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition-colors"
              >
                {tag}
              </button>
            )
          )}
        </div>
      </div>

      {/* Evidence Results List */}
      <div className="space-y-3">
        {results.length > 0 ? (
          results.map((chunk) => (
            <div
              key={chunk.id}
              className="bg-white border border-slate-200 rounded-md p-5 space-y-3 hover:border-slate-300 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 border-b border-slate-100 pb-2">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{chunk.title}</h3>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-1">
                    <span>{chunk.authors}</span>
                    <span>•</span>
                    <span className="font-medium text-slate-700">{chunk.source} ({chunk.publication_year})</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <span className="px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded font-mono text-xs font-semibold">
                    {chunk.citation_reference}
                  </span>
                  {chunk.relevance_score !== undefined && (
                    <span className="text-[11px] text-slate-400 font-mono">
                      Sim: {(chunk.relevance_score * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>

              {/* Excerpt */}
              <p className="text-xs text-slate-700 leading-relaxed bg-slate-50/70 p-3 rounded border border-slate-100 font-serif">
                "{chunk.content}"
              </p>
            </div>
          ))
        ) : (
          <div className="bg-white border border-slate-200 rounded-md p-8 text-center text-slate-400 text-xs">
            {loading ? 'Searching literature vector store...' : 'No literature matches found for this query.'}
          </div>
        )}
      </div>
    </div>
  );
};
