'use client';

import React from 'react';
import { ArrowRight, Terminal } from 'lucide-react';
import Link from 'next/link';

export default function DocsIntroductionPage() {
  return (
    <article className="prose prose-neutral dark:prose-invert max-w-none">
      
      <div className="mb-10 border-b border-neutral-200 dark:border-neutral-800 pb-8">
        <p className="text-[#F08787] font-mono text-sm font-medium mb-2">Documentation</p>
        <h1 className="text-4xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50 mb-4">
          Introduction
        </h1>
        <p className="text-xl text-neutral-600 dark:text-neutral-400 leading-relaxed">
          Engram is a local-first AI operating system designed for high-liability environments. 
          It runs completely offline, turning your machine into a private intelligence hub.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 not-prose mb-12">
        <Card 
          title="Quickstart Guide" 
          description="Get Engram running on macOS or Linux in under 5 minutes."
          href="/docs/installation"
        />
        <Card 
          title="Architecture" 
          description="Learn how the local vector database and inference engine work."
          href="/docs/architecture"
        />
      </div>

      <div className="space-y-6 text-neutral-700 dark:text-neutral-300">
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mt-12">Why Engram?</h2>
        <p>
          Most AI tools operate in the cloud, sending your sensitive logic, code, and personal data to remote servers. 
          Engram inverts this model.
        </p>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong>Local-First:</strong> Weights, biases, and vectors never leave your device.</li>
          <li><strong>Air-Gapped Ready:</strong> Once installed, zero internet connection is required.</li>
          <li><strong>High Performance:</strong> Native optimization for Apple Silicon (Metal) and NVIDIA GPUs (CUDA for Linux & Windows).</li>
        </ul>

        <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mt-12">System Requirements</h2>
        <div className="bg-neutral-100 dark:bg-[#111] p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 font-mono text-sm overflow-x-auto">
          <div className="flex gap-12 min-w-max">
            <div>
              <span className="block text-neutral-500 text-xs uppercase mb-1">RAM</span>
              <span className="font-semibold text-neutral-900 dark:text-white">16GB Unified (Min)</span>
            </div>
            <div>
              <span className="block text-neutral-500 text-xs uppercase mb-1">Storage</span>
              <span className="font-semibold text-neutral-900 dark:text-white">20GB SSD</span>
            </div>
            <div>
              <span className="block text-neutral-500 text-xs uppercase mb-1">OS</span>
              <span className="font-semibold text-neutral-900 dark:text-white">
                macOS 14+ / Windows 10+ (WSL2) / Linux</span>
            </div>
          </div>
        </div>
      </div>

    </article>
  );
}

function Card({ title, description, href }: { title: string; description: string; href: string }) {
  return (
    <Link 
      href={href}
      className="group p-6 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#111] hover:border-[#F08787]/50 transition-all"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-neutral-900 dark:text-white">{title}</h3>
        <ArrowRight className="w-4 h-4 text-neutral-400 group-hover:text-[#F08787] transition-colors" />
      </div>
      <p className="text-sm text-neutral-500 leading-relaxed">
        {description}
      </p>
    </Link>
  );
}