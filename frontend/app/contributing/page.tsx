'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  GitPullRequest, 
  Terminal, 
  Shield, 
  Cpu, 
  Eye, 
  Copy, 
  CheckCircle2, 
  AlertTriangle,
  FileCode,
  Server
} from 'lucide-react';

export default function ContributingPage() {
  return (
    <main className="min-h-screen pt-32 pb-20 px-6 bg-[#FAFAFA] dark:bg-[#0A0A0A] text-neutral-900 dark:text-neutral-50 font-sans">
      
      <div className="max-w-3xl mx-auto mb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F08787]/10 text-[#F08787] text-xs font-mono font-medium mb-6">
          <GitPullRequest className="w-3 h-3" />
          <span>Open Source</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">
          Contribute to Engram
        </h1>
        <p className="text-xl text-neutral-600 dark:text-neutral-400 leading-relaxed">
          Help us build the first truly private AI Operating System. 
          We welcome engineers, designers, and thinkers who share our vision of <span className="text-neutral-900 dark:text-white font-semibold">0% Data Egress</span>.
        </p>
      </div>

      <section className="max-w-3xl mx-auto mb-20">
        <h2 className="text-2xl font-bold mb-8 flex items-center gap-3">
          <Shield className="w-6 h-6 text-[#F08787]" />
          Core Philosophy
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <PhilosophyCard 
            icon={Cpu}
            title="Local-First"
            description="All inference happens on metal. No API calls to OpenAI/Anthropic for core logic."
          />
          <PhilosophyCard 
            icon={Shield}
            title="Privacy by Design"
            description="User data, files, and memories must never leave the Docker container."
          />
          <PhilosophyCard 
            icon={Eye}
            title="Transparent Action"
            description="Agents never take high-stakes actions without user review and clear logs."
          />
        </div>
      </section>

      <section className="max-w-3xl mx-auto mb-20">
        <h2 className="text-2xl font-bold mb-8">The Tech Stack</h2>
        <div className="bg-white dark:bg-[#111] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-8 gap-x-12">
            <StackItem label="Backend" value="Python 3.11" detail="FastAPI, Celery, Watchdog" />
            <StackItem label="Frontend" value="TypeScript" detail="Next.js 14, Tailwind, Framer Motion" />
            <StackItem label="Infrastructure" value="Docker Compose" detail="Redis, Qdrant Vector DB" />
            <StackItem label="AI Engine" value="Ollama" detail="Llama 3.1 8B (Quantized)" />
          </div>
        </div>
      </section>

      <section className="max-w-3xl mx-auto mb-20">
        <h2 className="text-2xl font-bold mb-8 flex items-center gap-3">
          <Terminal className="w-6 h-6 text-[#F08787]" />
          Local Development Setup
        </h2>
        
        <div className="space-y-12 border-l border-neutral-200 dark:border-neutral-800 pl-8 ml-3">
          
          <Step 
            number="01" 
            title="Clone & Configure"
            description="Get the repository and create the necessary inbox structure for document processing."
          >
            <CodeBlock>
              git clone https://github.com/VS251/engram-os.git{"\n"}
              cd engram-os{"\n"}
              mkdir -p AI_Inbox/processed
            </CodeBlock>
          </Step>

          <Step 
            number="02" 
            title="Setup Secrets"
            description="Obtain credentials.json from Google Cloud Console (Calendar + Gmail scopes) and place it in root."
          >
            <CodeBlock>
              pip install google-auth-oauthlib{"\n"}
              python3 generate_token.py
            </CodeBlock>
          </Step>

          <Step 
            number="03" 
            title="Run the Backend"
            description="Boot the API, Worker, Database, and Dashboard using the provided lifecycle script."
          >
            <CodeBlock>
              chmod +x start_os.sh{"\n"}
              ./start_os.sh
            </CodeBlock>
          </Step>

          <Step 
            number="04" 
            title="Run the Frontend"
            description="If contributing to the UI or Marketing Site."
          >
            <CodeBlock>
              cd frontend{"\n"}
              npm install && npm run dev
            </CodeBlock>
          </Step>

        </div>
      </section>

      <section className="max-w-3xl mx-auto mb-20">
        <div className="p-8 rounded-2xl bg-neutral-100 dark:bg-[#111] border border-neutral-200 dark:border-neutral-800">
          <h3 className="text-xl font-bold mb-6">Ready to Submit?</h3>
          <ul className="space-y-4">
            <CheckItem text="Fork repository & create a descriptive branch (feat/email-agent)." />
            <CheckItem text="Ensure docker-compose up builds cleanly without errors." />
            <CheckItem text="Format code: PEP 8 for Python, Prettier for TypeScript." />
            <CheckItem text="Include screenshots for any UI-related changes." />
          </ul>
        </div>
      </section>

      <section className="max-w-3xl mx-auto text-center border-t border-neutral-200 dark:border-neutral-800 pt-12">
        <h3 className="text-lg font-bold mb-2">Found a bug?</h3>
        <p className="text-neutral-600 dark:text-neutral-400 mb-6">
          Please include your OS, Docker status, and relevant logs in the issue description.
        </p>
        <button className="px-6 py-2.5 rounded-xl bg-neutral-900 dark:bg-white text-white dark:text-black font-medium text-sm hover:opacity-90 transition-opacity">
          Open an Issue
        </button>
      </section>

    </main>
  );
}


function PhilosophyCard({ icon: Icon, title, description }: { icon: any, title: string, description: string }) {
  return (
    <div className="p-6 rounded-2xl bg-white dark:bg-[#111] border border-neutral-200 dark:border-neutral-800">
      <div className="w-10 h-10 rounded-lg bg-neutral-50 dark:bg-neutral-900 flex items-center justify-center mb-4 text-[#F08787]">
        <Icon className="w-5 h-5" />
      </div>
      <h3 className="font-bold mb-2">{title}</h3>
      <p className="text-sm text-neutral-500 leading-relaxed">{description}</p>
    </div>
  );
}

function StackItem({ label, value, detail }: { label: string, value: string, detail: string }) {
  return (
    <div>
      <span className="block text-xs uppercase tracking-wider text-neutral-400 mb-1 font-mono">{label}</span>
      <div className="font-semibold text-lg">{value}</div>
      <div className="text-sm text-neutral-500">{detail}</div>
    </div>
  );
}

function Step({ number, title, description, children }: { number: string, title: string, description: string, children: React.ReactNode }) {
  return (
    <div className="relative">
      <span className="absolute -left-[45px] top-0 font-mono text-sm text-neutral-300 dark:text-neutral-700 font-bold">
        {number}
      </span>
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-neutral-600 dark:text-neutral-400 mb-6 max-w-xl">
        {description}
      </p>
      {children}
    </div>
  );
}

function CodeBlock({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative group">
      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
        <button className="p-1.5 rounded-md hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors">
          <Copy className="w-4 h-4" />
        </button>
      </div>
      <pre className="bg-[#1e1e1e] text-neutral-200 p-5 rounded-xl font-mono text-sm overflow-x-auto border border-neutral-800 shadow-sm">
        {children}
      </pre>
    </div>
  );
}

function CheckItem({ text }: { text: string }) {
  return (
    <li className="flex items-start gap-3">
      <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
      <span className="text-neutral-700 dark:text-neutral-300">{text}</span>
    </li>
  );
}