import React from 'react';
import {
  LayoutDashboard,
  Atom,
  Database,
  Sparkles,
  FlaskConical,
  Cpu,
  BookOpen,
  Brain,
  ListTodo,
  Settings,
  ShieldCheck,
  Search,
} from 'lucide-react';

interface AppShellProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentTab,
  onSelectTab,
  children,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { section: 'WORKSPACE' },
    { id: 'molecules', label: 'Molecules', icon: Atom },
    { id: 'datasets', label: 'Datasets', icon: Database },
    { id: 'predictions', label: 'Predictions', icon: Sparkles },
    { id: 'experiments', label: 'Experiments', icon: FlaskConical },
    { id: 'models', label: 'Models', icon: Cpu },
    { section: 'RESEARCH' },
    { id: 'literature', label: 'Literature', icon: BookOpen },
    { id: 'rag', label: 'Scientific RAG', icon: Brain },
    { section: 'SYSTEM' },
    { id: 'jobs', label: 'Jobs', icon: ListTodo },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar */}
      <aside className="w-60 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 select-none">
        <div>
          {/* Logo Brand */}
          <div className="h-14 flex items-center px-5 border-b border-slate-200">
            <div className="flex items-center space-x-2.5">
              <div className="w-7 h-7 bg-emerald-600 rounded flex items-center justify-center text-white font-bold text-sm shadow-xs">
                BF
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-sm tracking-tight text-slate-900">BioForge</span>
                <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
                  Molecular AI
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1 overflow-y-auto max-h-[calc(100vh-140px)]">
            {navItems.map((item, idx) => {
              if (item.section) {
                return (
                  <div
                    key={`sec-${idx}`}
                    className="pt-4 pb-1 px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider"
                  >
                    {item.section}
                  </div>
                );
              }

              const Icon = item.icon!;
              const isActive = currentTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id!)}
                  className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-800 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                  }`}
                >
                  <Icon
                    size={16}
                    className={isActive ? 'text-emerald-700' : 'text-slate-400'}
                  />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* User / Workspace footer */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/50">
          <div className="flex items-center justify-between px-2 py-1.5 rounded-md text-xs text-slate-500">
            <div className="flex items-center space-x-2">
              <ShieldCheck size={14} className="text-emerald-600" />
              <span className="font-medium text-slate-700">Lab Node 01</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">v0.1.0</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-4">
            <h1 className="text-sm font-bold text-slate-800 tracking-tight capitalize">
              {currentTab === 'rag' ? 'Scientific RAG' : currentTab}
            </h1>
            <span className="text-slate-300">|</span>
            <span className="text-xs text-slate-500">
              Delaney ESOL Benchmark • RDKit 2026.3 • PyTorch GNN
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search
                size={14}
                className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                placeholder="Search compound, SMILES, DOI..."
                className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-emerald-500 focus:bg-white w-64 text-slate-800 placeholder-slate-400 transition-all"
              />
            </div>

            <button
              onClick={() => onSelectTab('predictions')}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold shadow-xs transition-colors"
            >
              New Prediction
            </button>
          </div>
        </header>

        {/* Scrollable View Container */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50/70">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
};
