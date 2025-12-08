"use client";

import { motion } from "framer-motion";
import { FileCode, Database, Terminal, Zap, Lock, Cpu } from "lucide-react";

export default function ArchitectureGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto p-4">
      
      {/* CARD 1: INGESTION ENGINE */}
      <motion.div 
        whileHover={{ y: -5 }}
        className="col-span-1 md:col-span-1 bg-[#1a1a1a] rounded-2xl border border-gray-800 overflow-hidden flex flex-col h-80 shadow-2xl"
      >
        
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-2 text-gray-400 text-sm font-mono">
                <FileCode size={16} className="text-blue-400"/>
                ingestor.py
            </div>
            <div className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-1 rounded border border-blue-500/20">
                Watchdog
            </div>
        </div>
        
        <div className="p-5 font-mono text-xs leading-relaxed text-gray-300 opacity-80">
            <div><span className="text-purple-400">class</span> <span className="text-yellow-300">FileHandler</span>(FileSystemEventHandler):</div>
            <div className="pl-4"><span className="text-purple-400">def</span> <span className="text-blue-300">on_modified</span>(self, event):</div>
            <div className="pl-8 text-gray-500"># Triggered instantly on save</div>
            <div className="pl-8"><span className="text-purple-400">if</span> event.src_path.endswith(<span className="text-green-400">".pdf"</span>):</div>
            <div className="pl-12">vectorize_local(event.src_path)</div>
            <div className="pl-12 text-green-400">print(f"Ingesting &#123;event.src_path&#125;")</div>
        </div>
        
        <div className="mt-auto p-4 bg-black/20 border-t border-gray-800">
            <div className="flex items-center gap-2 text-xs text-gray-500">
                <Zap size={12} className="text-yellow-500 fill-yellow-500" />
                <span>Latency: &lt; 50ms detection</span>
            </div>
        </div>
      </motion.div>


      {/* CARD 2: VECTOR STORE */}
      <motion.div 
        whileHover={{ y: -5 }}
        className="col-span-1 md:col-span-1 bg-[#1a1a1a] rounded-2xl border border-gray-800 overflow-hidden flex flex-col h-80 shadow-2xl"
      >
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-2 text-gray-400 text-sm font-mono">
                <Database size={16} className="text-red-400"/>
                qdrant_local
            </div>
            <div className="text-[10px] bg-red-500/10 text-red-400 px-2 py-1 rounded border border-red-500/20">
                Vector DB
            </div>
        </div>
        <div className="p-5 flex items-center justify-center h-full relative overflow-hidden">
            
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
        
            <div className="grid grid-cols-4 gap-2 opacity-50">
                {[...Array(16)].map((_, i) => (
                    <motion.div 
                        key={i}
                        initial={{ opacity: 0.3 }}
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ duration: 2, delay: i * 0.1, repeat: Infinity }}
                        className="w-8 h-8 rounded bg-red-500/20 border border-red-500/30 text-[8px] flex items-center justify-center text-red-300 font-mono"
                    >
                        0.{10 + (i * 6) % 89} 
                    </motion.div>
                ))}
            </div>
        </div>
        <div className="p-4 bg-black/20 border-t border-gray-800">
            <div className="flex items-center gap-2 text-xs text-gray-500">
                <Lock size={12} className="text-green-500" />
                <span>Zero-Knowledge Storage</span>
            </div>
        </div>
      </motion.div>


      {/* CARD 3: LOCAL INFERENCE */}
      <motion.div 
        whileHover={{ y: -5 }}
        className="col-span-1 md:col-span-1 bg-[#1a1a1a] rounded-2xl border border-gray-800 overflow-hidden flex flex-col h-80 shadow-2xl"
      >
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-2 text-gray-400 text-sm font-mono">
                <Terminal size={16} className="text-green-400"/>
                terminal
            </div>
            <div className="text-[10px] bg-green-500/10 text-green-400 px-2 py-1 rounded border border-green-500/20">
                Ollama
            </div>
        </div>
        <div className="p-5 font-mono text-xs leading-relaxed text-gray-300">
            <div className="mb-2"><span className="text-green-400">➜</span>  <span className="text-cyan-300"></span>ollama run llama3</div>
            <div className="text-gray-500 mb-2">loading model... done</div>
            <div>
                <span className="text-purple-400">user:</span> summarize budget.xlsx
            </div>
            <div className="mt-2">
                <span className="text-green-400">assistant:</span> Reading local context... 
                <motion.span 
                    animate={{ opacity: [0, 1, 0] }} 
                    transition={{ repeat: Infinity, duration: 0.8 }}
                    className="inline-block w-2 h-4 bg-green-400 ml-1 align-middle"
                />
            </div>
        </div>
        <div className="mt-auto p-4 bg-black/20 border-t border-gray-800">
            <div className="flex items-center gap-2 text-xs text-gray-500">
                <Cpu size={12} className="text-purple-500" />
                <span>CUDA Accelerated</span>
            </div>
        </div>
      </motion.div>

    </div>
  );
}