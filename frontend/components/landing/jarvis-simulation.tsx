"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Terminal,
  Cpu,
  FileSpreadsheet,
  Mail,
  CheckCircle2,
  Copy,
  Loader2,
  ArrowRight
} from "lucide-react";

const STEPS = {
  IDLE: 0,
  MOVE_TO_INPUT: 1,
  TYPING: 2,
  PROCESSING_1: 3, 
  PROCESSING_2: 4, 
  PROCESSING_3: 5, 
  SHOW_OUTPUT: 6,
  MOVE_TO_ACTION: 7,
  CLICK_ACTION: 8,
  FINISHED: 9
};

const PROMPT_TEXT = "Draft an email to Alex Chen. Reference Rust experience from LinkedIn and propose compensation based on 'budget_2025.xlsx' Senior Engineer band.";

export default function JarvisSimulation() {
  const [step, setStep] = useState(STEPS.IDLE);
  const [typedText, setTypedText] = useState("");

  useEffect(() => {
    let isMounted = true;
    const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    const run = async () => {
        setStep(STEPS.IDLE);
        setTypedText("");
        await wait(1000);

        if (!isMounted) return;
        setStep(STEPS.MOVE_TO_INPUT);
        await wait(800);

        if (!isMounted) return;
        setStep(STEPS.TYPING);
        for (let i = 0; i <= PROMPT_TEXT.length; i++) {
            if (!isMounted) break;
            setTypedText(PROMPT_TEXT.slice(0, i));
            await wait(45); 
        }
        await wait(500);

        if (!isMounted) return;
        setStep(STEPS.PROCESSING_1);
        await wait(1200);

        if (!isMounted) return;
        setStep(STEPS.PROCESSING_2);
        await wait(1200);

        if (!isMounted) return;
        setStep(STEPS.PROCESSING_3);
        await wait(1500);

        if (!isMounted) return;
        setStep(STEPS.SHOW_OUTPUT);
        await wait(1000);

        if (!isMounted) return;
        setStep(STEPS.MOVE_TO_ACTION);
        await wait(800);

        if (!isMounted) return;
        setStep(STEPS.CLICK_ACTION);
        await wait(3000); 

        if (!isMounted) return;
        setStep(STEPS.FINISHED);
    };
    run();
    return () => { isMounted = false; };
  }, []);

  const getCursorPos = () => {
    switch(step) {
      case STEPS.IDLE: return { left: "50%", top: "120%" };
      case STEPS.MOVE_TO_INPUT: return { left: "8%", top: "28%" };
      case STEPS.TYPING: return { left: "8%", top: "28%" };
      case STEPS.PROCESSING_1: return { left: "8%", top: "28%" };
      case STEPS.PROCESSING_2: return { left: "8%", top: "28%" };
      case STEPS.PROCESSING_3: return { left: "8%", top: "28%" };
      case STEPS.SHOW_OUTPUT: return { left: "50%", top: "60%" };
      case STEPS.MOVE_TO_ACTION: return { left: "90%", top: "40%" };
      case STEPS.CLICK_ACTION: return { left: "90%", top: "40%", scale: 0.9 };
      case STEPS.FINISHED: return { left: "90%", top: "90%" };
      default: return { left: "50%", top: "120%" };
    }
  };
  const cursor = getCursorPos();

  return (
    <div className="relative w-full h-full bg-[#1E1E1E] overflow-hidden font-mono text-sm text-gray-300 select-none flex flex-col p-6">
      
      <div className="flex items-center gap-3 pb-4 border-b border-gray-800 mb-6">
        <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg">
            <Terminal size={18} />
        </div>
        <h2 className="font-bold text-white tracking-wide">ENGRAM CORE :: AGENT_JARVIS</h2>
        <div className="ml-auto flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/50" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
            <div className="w-3 h-3 rounded-full bg-green-500/50" />
        </div>
      </div>

     
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[#F08787] mb-2 font-bold">
            <ArrowRight size={14} /> COMMAND
        </div>
        <div className="bg-black/30 p-3 rounded-lg border border-gray-800 flex items-center h-12">
            <span className="text-gray-500 mr-2">$</span>
            <span className="text-gray-100">{typedText}</span>
            {step === STEPS.TYPING && <span className="w-2 h-5 bg-[#F08787] animate-pulse ml-1"/>}
        </div>
      </div>

      
      <AnimatePresence>
        {step >= STEPS.PROCESSING_1 && step < STEPS.SHOW_OUTPUT && ( 
            <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-4 space-y-3"
            >
                <div className="flex items-center gap-2 text-purple-400 mb-2 font-bold">
                    <Cpu size={14} /> EXECUTION_LOG
                </div>
                <div className="space-y-2 text-xs font-medium">
                    
                    <div className="flex items-center gap-3">
                        {step === STEPS.PROCESSING_1 ? <Loader2 size={12} className="animate-spin text-[#F08787]"/> : <CheckCircle2 size={12} className="text-green-500"/>}
                        <span className={step > STEPS.PROCESSING_1 ? "text-gray-500" : "text-gray-100"}>
                            Reading memory: <span className="text-purple-300">linkedin_alex_chen</span>
                        </span>
                    </div>
                    
                    {step >= STEPS.PROCESSING_2 && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3">
                            {step === STEPS.PROCESSING_2 ? <Loader2 size={12} className="animate-spin text-[#F08787]"/> : <CheckCircle2 size={12} className="text-green-500"/>}
                            <span className={step > STEPS.PROCESSING_2 ? "text-gray-500" : "text-gray-100"}>
                                Opening local file: <span className="text-[#F08787] flex items-center gap-1"><FileSpreadsheet size={10}/> budget_2025.xlsx</span>
                            </span>
                        </motion.div>
                    )}
                    
                    {step >= STEPS.PROCESSING_3 && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3">
                            {step === STEPS.PROCESSING_3 ? <Loader2 size={12} className="animate-spin text-[#F08787]"/> : <CheckCircle2 size={12} className="text-green-500"/>}
                            <span className={step > STEPS.PROCESSING_3 ? "text-gray-500" : "text-gray-100"}>
                                Synthesizing action artifact...
                            </span>
                        </motion.div>
                    )}
                </div>
            </motion.div>
        )}
      </AnimatePresence>

      
      <AnimatePresence>
        {step >= STEPS.SHOW_OUTPUT && (
            <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex-1 bg-white text-gray-900 rounded-xl overflow-hidden flex flex-col shadow-2xl"
            >
                
                <div className="bg-gray-100 p-3 border-b border-gray-200 flex justify-between items-center shrink-0">
                    <div className="flex items-center gap-2">
                        <Mail size={16} className="text-gray-500" />
                        <span className="font-sans font-semibold text-xs">Draft: Engineering Role at Engram</span>
                    </div>
                    <motion.button 
                        animate={{ 
                            scale: step === STEPS.CLICK_ACTION ? 0.95 : 1,
                            backgroundColor: step >= STEPS.CLICK_ACTION ? "#22c55e" : "#F08787"
                        }}
                        className="flex items-center gap-2 px-3 py-1.5 bg-[#F08787] text-white rounded-md font-sans text-[10px] font-bold transition-colors"
                    >
                        {step >= STEPS.CLICK_ACTION ? <CheckCircle2 size={12}/> : <Copy size={12} />}
                        {step >= STEPS.CLICK_ACTION ? "Copied" : "Copy Draft"}
                    </motion.button>
                </div>
                
                
                <div className="p-5 font-sans text-xs leading-relaxed space-y-3 flex-1 overflow-y-auto">
                    <p>Hi Alex,</p>
                    <p>I hope this email finds you well. I came across your profile recently and was deeply impressed by your experience building high-scale <span className="bg-purple-100 px-1 rounded font-medium text-purple-800">Rust</span> infrastructure at Netflix.</p>
                    <p>We are building Engram, an AI operating system, and we are looking for a Senior Systems Engineer to lead our core backend team.</p>
                    <p>Regarding compensation, for this Senior level role, our budget is a base salary between <span className="bg-green-100 px-1 rounded font-medium text-green-800">$180k - $220k</span>, plus significant equity.</p>
                    <p>Are you open to a brief chat later this week?</p>
                    <p className="pt-2 text-gray-500">Best,<br/>[Your Name]</p>
                </div>
            </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        className="absolute z-50 pointer-events-none will-change-transform"
        style={{ filter: "drop-shadow(0 4px 6px rgba(0,0,0,0.15))" }}
        initial={{ left: "50%", top: "120%" }}
        animate={{ left: cursor.left, top: cursor.top, scale: cursor.scale || 1 }}
        transition={{ type: "tween", ease: "easeInOut", duration: 0.8 }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M3 3L10.07 19.97L12.58 12.58L19.97 10.07L3 3Z" fill="#1a1a1a" stroke="white" strokeWidth="2"/></svg>
      </motion.div>

    </div>
  );
}