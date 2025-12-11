'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  Github, 
  Chrome, 
  FileText, 
  Database, 
  Terminal, 
  Code, 
  Bot, 
  Layers,
  Plus
} from 'lucide-react';

type IntegrationStatus = 'live' | 'beta' | 'planned';
type Category = 'All' | 'Knowledge' | 'Models' | 'Developer';

interface Integration {
  id: string;
  name: string;
  description: string;
  category: Category;
  status: IntegrationStatus;
  icon: React.ElementType;
  developer: string;
}

const integrations: Integration[] = [
  {
    id: 'obsidian',
    name: 'Obsidian Vault',
    description: 'Index local Markdown files and canvas diagrams directly from disk. No plugin required.',
    category: 'Knowledge',
    status: 'live',
    icon: FileText,
    developer: 'Obsidian'
  },
  {
    id: 'pdf-engine',
    name: 'Local PDF Engine',
    description: 'High-performance PDF parsing with layout preservation and OCR capabilities.',
    category: 'Knowledge',
    status: 'live',
    icon: Layers,
    developer: 'Native'
  },
  {
    id: 'notion',
    name: 'Notion',
    description: 'Securely sync Notion pages to local storage for offline RAG usage.',
    category: 'Knowledge',
    status: 'planned',
    icon: Database,
    developer: 'Notion'
  },
  
  {
    id: 'vscode',
    name: 'VS Code Extension',
    description: 'Context-aware code completion and "Explain this snippet" directly in your editor.',
    category: 'Developer',
    status: 'beta',
    icon: Code,
    developer: 'Microsoft'
  },
  {
    id: 'terminal',
    name: 'CLI Suite',
    description: 'Pipe stdout directly into Engram for error analysis and log parsing.',
    category: 'Developer',
    status: 'live',
    icon: Terminal,
    developer: 'Native'
  },
  {
    id: 'github',
    name: 'GitHub Repos',
    description: 'Index remote repositories for chat-with-code functionality.',
    category: 'Developer',
    status: 'beta',
    icon: Github,
    developer: 'GitHub'
  },

  {
    id: 'ollama',
    name: 'Ollama Bridge',
    description: 'Offload inference to an existing Ollama instance running on port 11434.',
    category: 'Models',
    status: 'live',
    icon: Bot,
    developer: 'Ollama'
  },
  {
    id: 'huggingface',
    name: 'Hugging Face',
    description: 'Direct model discovery and quantization pipeline download.',
    category: 'Models',
    status: 'planned',
    icon: Search,
    developer: 'Hugging Face'
  },
  {
    id: 'chrome',
    name: 'Browser Context',
    description: 'Read the active tab content for summarization and extraction.',
    category: 'Knowledge',
    status: 'planned',
    icon: Chrome,
    developer: 'Google'
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 }
};

export default function IntegrationsPage() {
  const [activeCategory, setActiveCategory] = useState<Category>('All');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredIntegrations = integrations.filter(item => {
    const matchesCategory = activeCategory === 'All' || item.category === activeCategory;
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          item.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <main className="min-h-screen pt-32 pb-20 px-6 bg-[#FAFAFA] dark:bg-[#0A0A0A] text-neutral-900 dark:text-neutral-50 font-sans">
      
      <div className="max-w-6xl mx-auto mb-16">
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12"
        >
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-4">Integrations</h1>
            <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-xl">
              Connect Engram to your existing workflows. <br />
              Local-first data pipelines, zero data egress.
            </p>
          </div>
          
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
            <input 
              type="text" 
              placeholder="Search integrations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-white dark:bg-[#111] border border-neutral-200 dark:border-neutral-800 focus:outline-none focus:ring-2 focus:ring-[#F08787]/50 transition-all text-sm"
            />
          </div>
        </motion.div>

        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {['All', 'Knowledge', 'Developer', 'Models'].map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat as Category)}
              className={`
                px-4 py-1.5 rounded-full text-sm font-medium transition-all whitespace-nowrap
                ${activeCategory === cat 
                  ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900' 
                  : 'bg-neutral-100 dark:bg-neutral-900 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-800'}
              `}
            >
              {cat}
            </button>
          ))}
        </div>

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {filteredIntegrations.map((item) => (
            <IntegrationCard key={item.id} item={item} />
          ))}

          <motion.button 
            variants={itemVariants}
            className="group flex flex-col items-center justify-center p-8 rounded-2xl border border-dashed border-neutral-300 dark:border-neutral-700 hover:border-[#F08787] hover:bg-[#F08787]/5 transition-all text-center min-h-[240px]"
          >
            <div className="w-12 h-12 rounded-full bg-neutral-100 dark:bg-neutral-900 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Plus className="w-6 h-6 text-neutral-400 group-hover:text-[#F08787]" />
            </div>
            <h3 className="font-semibold mb-2">Request Integration</h3>
            <p className="text-sm text-neutral-500 max-w-[200px]">
              Don't see your tool? Vote for the next connector on our roadmap.
            </p>
          </motion.button>
        </motion.div>
      </div>
    </main>
  );
}

function IntegrationCard({ item }: { item: Integration }) {
  const Icon = item.icon;
  
  const statusColors = {
    live: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
    beta: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
    planned: 'bg-neutral-100 dark:bg-neutral-800 text-neutral-500 border-neutral-200 dark:border-neutral-700'
  };

  const statusLabels = {
    live: 'Available',
    beta: 'Public Beta',
    planned: 'Coming Soon'
  };

  return (
    <motion.div 
      variants={itemVariants}
      className="flex flex-col p-6 rounded-2xl bg-white dark:bg-[#111] border border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 transition-colors"
    >
      <div className="flex items-start justify-between mb-6">
        <div className="w-10 h-10 rounded-lg bg-neutral-50 dark:bg-neutral-900 flex items-center justify-center border border-neutral-100 dark:border-neutral-800">
          <Icon className="w-5 h-5 text-neutral-700 dark:text-neutral-300" />
        </div>
        <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wide font-bold border ${statusColors[item.status]}`}>
          {statusLabels[item.status]}
        </span>
      </div>
      
      <h3 className="text-lg font-bold mb-2">{item.name}</h3>
      <p className="text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed mb-6 flex-grow">
        {item.description}
      </p>

      <div className="pt-4 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between text-xs text-neutral-400">
        <span>by {item.developer}</span>
        {item.status !== 'planned' && (
          <button className="text-neutral-900 dark:text-white font-medium hover:underline">
            Configure &rarr;
          </button>
        )}
      </div>
    </motion.div>
  );
}