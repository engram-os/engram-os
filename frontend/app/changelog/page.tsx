'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { GitCommit, Tag, Sparkles, Wrench, Bug } from 'lucide-react';

type ChangeType = 'feature' | 'improvement' | 'fix';

interface ChangeItem {
  type: ChangeType;
  content: string;
}

interface Release {
  version: string;
  date: string;
  title: string;
  description?: string;
  changes: ChangeItem[];
  isLatest?: boolean;
}

const releases: Release[] = [
  {
    version: 'v0.9.2',
    date: 'December 10, 2025',
    title: 'The Interface Update',
    description: 'A complete overhaul of the design system, migrating to Tailwind v4 and implementing the new "Tech-Noir" aesthetic.',
    isLatest: true,
    changes: [
      { type: 'feature', content: 'Migrated frontend architecture to Next.js 15 App Router.' },
      { type: 'feature', content: 'Introduced "Tech-Noir" dark/light hybrid theme.' },
      { type: 'improvement', content: 'Implemented Framer Motion for non-blocking UI transitions.' },
      { type: 'fix', content: 'Resolved hydration mismatch in the Sticky Header component.' }
    ]
  },
  {
    version: 'v0.9.0',
    date: 'November 28, 2025',
    title: 'Core Engine Beta',
    description: 'First stable build of the local inference engine using Llama 3.1 8B quantized models.',
    changes: [
      { type: 'feature', content: 'Local-first RAG pipeline is now operational.' },
      { type: 'feature', content: 'Added support for .md and .txt file ingestion.' },
      { type: 'improvement', content: 'Vector database initialization time reduced by 60%.' }
    ]
  },
  {
    version: 'v0.1.0',
    date: 'November 1, 2025',
    title: 'Project Inception',
    changes: [
      { type: 'feature', content: 'Initial repository setup and architecture planning.' },
      { type: 'feature', content: 'Proof of concept: "CodeVault" code explainer tool.' }
    ]
  }
];

export default function ChangelogPage() {
  return (
    <main className="min-h-screen pt-32 pb-20 px-6 bg-[#FAFAFA] dark:bg-[#0A0A0A] text-neutral-900 dark:text-neutral-50 font-sans">
      
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-3xl mx-auto mb-16"
      >
        <h1 className="text-4xl font-bold tracking-tight mb-4">Changelog</h1>
        <p className="text-lg text-neutral-600 dark:text-neutral-400">
          Tracking the evolution of the Engram Operating System.
        </p>
      </motion.div>

      <div className="max-w-3xl mx-auto relative">
        
        <div className="absolute left-[27px] top-4 bottom-0 w-px bg-neutral-200 dark:bg-neutral-800" />

        <div className="space-y-12">
          {releases.map((release, index) => (
            <ReleaseItem key={release.version} release={release} index={index} />
          ))}
        </div>
      </div>
    </main>
  );
}

function ReleaseItem({ release, index }: { release: Release; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ delay: index * 0.1 }}
      className="relative pl-20 group"
    >
      <div className={`
        absolute left-0 top-1.5 w-[55px] h-[32px] rounded-full border flex items-center justify-center text-[10px] font-mono font-medium z-10
        ${release.isLatest 
          ? 'bg-[#F08787] border-[#F08787] text-white shadow-[0_0_15px_rgba(240,135,135,0.4)]' 
          : 'bg-white dark:bg-[#0A0A0A] border-neutral-200 dark:border-neutral-800 text-neutral-500'}
      `}>
        {release.version}
      </div>

      <div className="text-sm font-mono text-neutral-400 mb-2 flex items-center gap-2">
        <GitCommit className="w-4 h-4" />
        {release.date}
      </div>

      <div className="
        p-6 rounded-2xl border bg-white dark:bg-[#111] border-neutral-200 dark:border-neutral-800
        transition-colors hover:border-neutral-300 dark:hover:border-neutral-700
      ">
        <h2 className="text-xl font-bold mb-2 flex items-center gap-3">
          {release.title}
          {release.isLatest && (
            <span className="px-2 py-0.5 rounded-full bg-[#F08787]/10 text-[#F08787] text-xs font-medium border border-[#F08787]/20">
              Latest
            </span>
          )}
        </h2>
        
        {release.description && (
          <p className="text-neutral-600 dark:text-neutral-400 mb-6 leading-relaxed">
            {release.description}
          </p>
        )}

        <ul className="space-y-3">
          {release.changes.map((change, i) => (
            <li key={i} className="flex items-start gap-3 text-sm">
              <ChangeIcon type={change.type} />
              <span className="text-neutral-700 dark:text-neutral-300 mt-0.5">
                {change.content}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}

function ChangeIcon({ type }: { type: ChangeType }) {
  switch (type) {
    case 'feature':
      return <Sparkles className="w-4 h-4 text-[#F08787] shrink-0" />;
    case 'improvement':
      return <Tag className="w-4 h-4 text-neutral-400 shrink-0" />;
    case 'fix':
      return <Wrench className="w-4 h-4 text-neutral-500 shrink-0" />;
  }
}