'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  ShieldAlert, 
  ServerOff, 
  FileWarning, 
  CheckCircle2, 
  Scale, 
  Lock,
  Stethoscope,
  Code2,
  Briefcase
} from 'lucide-react';
import Link from 'next/link';

export default function CaseStudyPage() {
  return (
    <main className="min-h-screen pt-32 pb-20 px-6 bg-[#FAFAFA] dark:bg-[#0A0A0A] text-neutral-900 dark:text-neutral-50 font-sans">
      
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto mb-24 text-center"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 dark:bg-red-900/10 text-red-600 dark:text-red-400 text-xs font-mono font-medium mb-8 border border-red-100 dark:border-red-900/30">
          <ShieldAlert className="w-3 h-3" />
          THREAT ANALYSIS
        </div>
        
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6 leading-tight">
          The High-Liability Gap
        </h1>
        
        <p className="text-xl text-neutral-600 dark:text-neutral-300 max-w-2xl mx-auto leading-relaxed">
          For 90% of users, Cloud AI is fine. <br />
          For the other 10%—healthcare, finance, and R&D—<span className="text-[#F08787] font-medium">data egress is a fireable offense.</span>
        </p>
      </motion.div>

      <div className="max-w-6xl mx-auto mb-32">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <RiskCard 
            icon={Code2}
            title="The IP Leak"
            sector="Semiconductors & R&D"
            risk="High"
            context="In 2023, engineers at a major tech firm pasted proprietary source code into a public LLM to optimize it. That code is now part of the model's training data, potentially accessible to competitors."
            solution="Engram indexes local repositories (Git) and runs Llama 3 on-device. Your IP never leaves the localhost loop."
          />

          <RiskCard 
            icon={Briefcase}
            title="The M&A Breach"
            sector="Legal & Finance"
            risk="Critical"
            context="Mergers & Acquisitions rely on strict confidentiality. Uploading a 'confidential_balance_sheet.pdf' to a cloud PDF parser for summarization violates NDA terms instantly."
            solution="Engram uses a local OCR engine to parse PDFs. The vector database (Qdrant) lives on your encrypted SSD."
          />

          <RiskCard 
            icon={Stethoscope}
            title="The HIPAA Violation"
            sector="Healthcare"
            risk="Critical"
            context="Doctors need AI to draft patient notes, but inputting PII (Personally Identifiable Information) into a web prompt violates HIPAA and GDPR compliance regulations."
            solution="Engram operates in an air-gapped environment. No data packet is ever sent to a third-party server, ensuring 100% compliance."
          />

        </div>
      </div>

      <motion.div 
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="max-w-4xl mx-auto mb-24"
      >
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">The Architecture of Trust</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Comparing the data lifecycle of a standard Cloud LLM vs. Engram.
          </p>
        </div>

        <div className="bg-white dark:bg-[#111] border border-neutral-200 dark:border-neutral-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="grid grid-cols-3 bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 p-4 font-mono text-xs font-bold uppercase tracking-wider text-neutral-500">
            <div>Vector</div>
            <div>Cloud AI (SaaS)</div>
            <div className="text-[#F08787]">Engram (Local)</div>
          </div>

          <ComparisonRow 
            label="Inference Location" 
            bad="Remote Server (California)" 
            good="Local GPU / CPU" 
          />
          <ComparisonRow 
            label="Data Persistence" 
            bad="Retained for Training (30 Days)" 
            good="Ephemeral (RAM Only)" 
          />
          <ComparisonRow 
            label="Internet Requirement" 
            bad="Constant Connection" 
            good="Zero (Air-Gap Ready)" 
          />
          <ComparisonRow 
            label="Vector Storage" 
            bad="Managed Cloud DB (Pinecone)" 
            good="Local File System (Qdrant)" 
          />
          <ComparisonRow 
            label="Cost Model" 
            bad="Per Token ($$$)" 
            good="One-time Hardware" 
          />
        </div>
      </motion.div>

      <div className="max-w-3xl mx-auto mb-20">
        <div className="p-8 rounded-3xl bg-neutral-900 text-neutral-300 relative overflow-hidden">
          <div className="relative z-10">
            <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
              <ServerOff className="w-6 h-6 text-[#F08787]" />
              The "Air-Gap" Guarantee
            </h3>
            <p className="mb-6 leading-relaxed text-neutral-400">
              True security isn't about better encryption keys; it's about physics. 
              If the wire is cut, the data cannot leak.
            </p>
            <p className="mb-8 leading-relaxed text-neutral-400">
              Engram is designed to function fully on a machine with <strong>Wi-Fi disabled</strong>. 
              Once the initial model weights (4GB) are downloaded, you can physically disconnect your device 
              and perform RAG (Retrieval Augmented Generation) on unlimited documents.
            </p>
            
            <Link 
              href="/docs/architecture"
              className="text-white font-medium border-b border-[#F08787] pb-0.5 hover:text-[#F08787] transition-colors"
            >
              Verify our Network Architecture &rarr;
            </Link>
          </div>

          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-[#F08787]/10 to-transparent rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />
        </div>
      </div>

    </main>
  );
}


function RiskCard({ title, sector, risk, context, solution, icon: Icon }: any) {
  return (
    <div className="flex flex-col p-8 rounded-2xl bg-white dark:bg-[#111] border border-neutral-200 dark:border-neutral-800 h-full">
      <div className="flex justify-between items-start mb-6">
        <div className="w-12 h-12 rounded-xl bg-neutral-50 dark:bg-neutral-900 flex items-center justify-center text-neutral-900 dark:text-white">
          <Icon className="w-6 h-6" strokeWidth={1.5} />
        </div>
        <span className="px-3 py-1 rounded-full bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs font-bold uppercase tracking-wide border border-red-100 dark:border-red-900/30">
          Risk: {risk}
        </span>
      </div>
      
      <h3 className="text-xl font-bold mb-1">{title}</h3>
      <p className="text-xs font-mono text-neutral-500 uppercase tracking-wider mb-6">{sector}</p>
      
      <div className="flex-grow">
        <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-6 leading-relaxed border-l-2 border-red-200 dark:border-red-900 pl-4">
          <span className="block font-semibold text-neutral-900 dark:text-white mb-1">The Incident:</span>
          "{context}"
        </p>
      </div>

      <div className="mt-6 pt-6 border-t border-neutral-100 dark:border-neutral-800">
        <p className="text-sm text-neutral-600 dark:text-neutral-300 leading-relaxed">
          <span className="block font-semibold text-[#F08787] mb-1 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> The Engram Fix:
          </span>
          {solution}
        </p>
      </div>
    </div>
  );
}

function ComparisonRow({ label, bad, good }: { label: string, bad: string, good: string }) {
  return (
    <div className="grid grid-cols-3 p-4 border-b border-neutral-100 dark:border-neutral-800 last:border-0 hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors">
      <div className="font-medium text-sm text-neutral-900 dark:text-white flex items-center">
        {label}
      </div>
      <div className="text-sm text-neutral-500 flex items-center gap-2">
        <FileWarning className="w-4 h-4 text-neutral-400 shrink-0" />
        {bad}
      </div>
      <div className="text-sm text-neutral-900 dark:text-white font-medium flex items-center gap-2">
        <Lock className="w-4 h-4 text-[#F08787] shrink-0" />
        {good}
      </div>
    </div>
  );
}