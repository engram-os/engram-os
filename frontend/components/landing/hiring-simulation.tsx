"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ShieldCheck, 
  Bot, 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle2, 
  Lock, 
  Briefcase,
  MapPin,
  MoreHorizontal,
  UserCheck,
  Search,
  Globe,
  LayoutGrid,
  Send,
  AppWindow,
  Disc
} from "lucide-react";

const STEPS = {
  BROWSER_HOME: 0,
  MOVE_TO_SEARCH_BAR: 1,
  TYPING_SEARCH: 2,
  CLICK_SEARCH: 3,
  SHOW_RESULTS: 4,
  CLICK_RESULT: 5,
  SHOW_PROFILE: 6,
  MOVE_TO_EXTENSION: 7,
  CLICK_EXTENSION: 8,
  SAVING: 9,
  MOVE_TO_DOCK: 10,
  CLICK_DOCK: 11,
  SHOW_APP: 12,
  MOVE_TO_APP_INPUT: 13,
  APP_TYPING: 14,
  MOVE_TO_SEND: 15,
  APP_SEND: 16,
  APP_THINKING: 17,
  APP_RESPONSE: 18,
};

const SEARCH_QUERY = "Alex Chen linkedin";
const APP_QUERY = "Fit check against hiring_reqs.md?";

export default function HiringSimulation() {
  const [step, setStep] = useState(STEPS.BROWSER_HOME);
  const [searchValue, setSearchValue] = useState("");
  const [appValue, setAppValue] = useState("");

  useEffect(() => {
    let isMounted = true;
    const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    const run = async () => {
        
        setStep(STEPS.BROWSER_HOME);
        setSearchValue("");
        setAppValue("");
        await wait(1000);

        if (!isMounted) return;
        setStep(STEPS.MOVE_TO_SEARCH_BAR);
        await wait(1000); 

        
        if (!isMounted) return;
        setStep(STEPS.TYPING_SEARCH);
        for (let i = 0; i <= SEARCH_QUERY.length; i++) {
            if (!isMounted) break;
            setSearchValue(SEARCH_QUERY.slice(0, i));
            await wait(50); 
        }
        await wait(500);

        
        if (!isMounted) return;
        setStep(STEPS.CLICK_SEARCH);
        await wait(1000);

        
        if (!isMounted) return;
        setStep(STEPS.SHOW_RESULTS);
        await wait(1000);

        
        if (!isMounted) return;
        setStep(STEPS.CLICK_RESULT);
        await wait(1000);

        
        if (!isMounted) return;
        setStep(STEPS.SHOW_PROFILE);
        await wait(1000);

        
        if (!isMounted) return;
        setStep(STEPS.MOVE_TO_EXTENSION);
        await wait(1000);

        
        if (!isMounted) return;
        setStep(STEPS.CLICK_EXTENSION);
        await wait(400);

        
        if (!isMounted) return;
        setStep(STEPS.SAVING);
        await wait(1000);

        
        if (!isMounted) return;
        setStep(STEPS.MOVE_TO_DOCK);
        await wait(1000);

        
        if (!isMounted) return;
        setStep(STEPS.CLICK_DOCK);
        await wait(500);

        
        if (!isMounted) return;
        setStep(STEPS.SHOW_APP);
        await wait(800);

        
        if (!isMounted) return;
        setStep(STEPS.MOVE_TO_APP_INPUT);
        await wait(800);

        
        if (!isMounted) return;
        setStep(STEPS.APP_TYPING);
        for (let i = 0; i <= APP_QUERY.length; i++) {
            if (!isMounted) break;
            setAppValue(APP_QUERY.slice(0, i));
            await wait(40);
        }
        await wait(1000);

        
        if (!isMounted) return;
        setStep(STEPS.MOVE_TO_SEND);
        await wait(1000);

        
        if (!isMounted) return;
        setStep(STEPS.APP_SEND);
        await wait(300);

        
        if (!isMounted) return;
        setStep(STEPS.APP_THINKING);
        await wait(2000);

        
        if (!isMounted) return;
        setStep(STEPS.APP_RESPONSE);
    };
    run();
    return () => { isMounted = false; };
  }, []);

  const getCursorPos = () => {
    switch(step) {
      case STEPS.BROWSER_HOME: return { left: "50%", top: "60%" };
      case STEPS.MOVE_TO_SEARCH_BAR: return { left: "65%", top: "44%" };
      case STEPS.TYPING_SEARCH: return { left: "65%", top: "44%" };
      case STEPS.CLICK_SEARCH: return { left: "40%", top: "55%", scale: 0.9 }; 
      case STEPS.SHOW_RESULTS: return { left: "40%", top: "55%" };
      case STEPS.CLICK_RESULT: return { left: "40%", top: "25%", scale: 0.9 }; 
      case STEPS.SHOW_PROFILE: return { left: "40%", top: "21%" };
      case STEPS.MOVE_TO_EXTENSION: return { left: "91%", top: "11%" };
      case STEPS.CLICK_EXTENSION: return { left: "91%", top: "11%", scale: 0.9 };
      case STEPS.SAVING: return { left: "91%", top: "11%" };
      case STEPS.MOVE_TO_DOCK: return { left: "54%", top: "92%" }; 
      case STEPS.CLICK_DOCK: return { left: "54%", top: "92%" };
      case STEPS.SHOW_APP: return { left: "54%", top: "92%" };
      case STEPS.MOVE_TO_APP_INPUT: return {left: "50%", top: "83%"};
      case STEPS.APP_TYPING: return { left: "50%", top: "83%" };
      case STEPS.MOVE_TO_SEND: return { left: "92%", top: "83%" };
      case STEPS.APP_SEND: return { left: "92%", top: "83%"}; 
      case STEPS.APP_THINKING: return { left: "90%", top: "90%" };
      case STEPS.APP_RESPONSE: return { left: "90%", top: "90%" };
      default: return { left: "50%", top: "120%" };
    }
  };
  const cursor = getCursorPos();

  return (
    <div className="relative w-full h-full bg-[#3D3D3D] overflow-hidden font-sans select-none flex flex-col items-center justify-center">
      
      
      <div className="absolute inset-0 z-0 bg-gradient-to-br from-rose-100 to-teal-100 opacity-20" />

      {/* --- LAYER 1: THE BROWSER --- */}
      <AnimatePresence>
        {step < STEPS.CLICK_DOCK && (
          <motion.div 
            initial={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.1 }}
            className="absolute w-[90%] h-[80%] bg-white rounded-xl shadow-2xl flex flex-col z-10 overflow-hidden"
            style={{ top: "8%" }}
          >
            
            <div className="h-10 bg-[#F3F4F6] border-b border-gray-200 flex items-center px-4 gap-4">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                <div className="w-3 h-3 rounded-full bg-green-400" />
              </div>
              <div className="flex gap-3 text-gray-400">
                <ArrowLeft size={14} />
                <ArrowRight size={14} />
              </div>
              
              
              <div className="flex-1 h-7 bg-white rounded-md border border-gray-200 flex items-center px-3 text-xs text-gray-600 gap-2 mx-2">
                <Lock size={10} className="text-gray-400" />
                {step < STEPS.SHOW_RESULTS ? "google.com" : 
                 step < STEPS.SHOW_PROFILE ? "google.com/search?q=alex+chen" : 
                 "linkedin.com/in/alex-chen"}
              </div>

              
              <div className="pl-3 border-l">
                 <div className="relative">
                    <motion.div 
                      animate={{ 
                        color: step >= STEPS.CLICK_EXTENSION ? "#F08787" : "#9CA3AF"
                      }}
                      className="p-1 rounded transition-colors"
                    >
                      <Bot size={16} />
                    </motion.div>
                    
                    <AnimatePresence>
                      {step === STEPS.SAVING && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0 }}
                          className="absolute top-8 right-0 w-48 bg-[#1a1a1a] text-white p-2 rounded shadow-xl text-[10px] z-50 whitespace-nowrap"
                        >
                          <div className="flex items-center gap-1 text-[#F08787] font-bold">
                            <CheckCircle2 size={10} /> Saved to Memory
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                 </div>
              </div>
            </div>

            
            <div className="flex-1 relative">
                
                
                {step < STEPS.SHOW_RESULTS && (
                    <div className="flex flex-col items-center justify-center h-full pb-20">
                        <div className="text-4xl font-bold mb-6 text-gray-700 flex gap-1">
                            <span className="text-blue-500">G</span>
                            <span className="text-red-500">o</span>
                            <span className="text-yellow-500">o</span>
                            <span className="text-blue-500">g</span>
                            <span className="text-green-500">l</span>
                            <span className="text-red-500">e</span>
                        </div>
                        <div className="w-[60%] h-10 border border-gray-300 rounded-full flex items-center px-4 shadow-sm hover:shadow-md transition-shadow">
                            <Search size={16} className="text-gray-400 mr-2" />
                            <div className="text-sm text-gray-800 flex-1">
                                {searchValue}
                                {step === STEPS.TYPING_SEARCH && <span className="animate-pulse">|</span>}
                            </div>
                        </div>
                        <div className="mt-6 flex gap-3">
                            <div className="bg-gray-50 px-4 py-2 rounded text-xs text-gray-600 border border-gray-100">Google Search</div>
                            <div className="bg-gray-50 px-4 py-2 rounded text-xs text-gray-600 border border-gray-100">I'm Feeling Lucky</div>
                        </div>
                    </div>
                )}

                {/* 2. RESULTS */}
                {step >= STEPS.SHOW_RESULTS && step < STEPS.SHOW_PROFILE && (
                    <div className="w-full h-full bg-white flex flex-col justify-start items-start text-left pt-6 pl-6 overflow-y-auto">
                         
                         {/* Result 1: The Target */}
                         <div className="mb-6 max-w-xl">
                            <div className="group cursor-pointer">
                                <div className="text-sm text-[#202124] mb-1 flex items-center gap-1">
                                    <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-[10px]">in</div>
                                    <div className="flex flex-col leading-none">
                                        <span className="text-[12px]">LinkedIn</span>
                                        <span className="text-[10px] text-gray-500">https://www.linkedin.com › in › alex-chen</span>
                                    </div>
                                </div>
                                <div className="text-xl text-[#1a0dab] group-hover:underline font-medium cursor-pointer">
                                    Alex Chen - Senior Systems Engineer - LinkedIn
                                </div>
                            </div>
                            <div className="text-sm text-[#4d5156] leading-relaxed mt-1">
                                San Francisco, CA · Senior Systems Engineer · Ex-Netflix. <br/>
                                View Alex Chen's profile on LinkedIn, the world's largest professional community. Alex has 8 jobs listed on their profile.
                            </div>
                         </div>

                         {/* Result 2: Portfolio */}
                         <div className="mb-6 max-w-xl opacity-80">
                            <div className="group cursor-pointer">
                                <div className="text-sm text-[#202124] mb-1 flex items-center gap-1">
                                    <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-[10px]">AC</div>
                                    <div className="flex flex-col leading-none">
                                        <span className="text-[12px]">Alex Chen Dev</span>
                                        <span className="text-[10px] text-gray-500">https://alexchen.dev</span>
                                    </div>
                                </div>
                                <div className="text-xl text-[#1a0dab] group-hover:underline font-medium cursor-pointer">
                                    Alex Chen | High-Scale Infrastructure
                                </div>
                            </div>
                            <div className="text-sm text-[#4d5156] leading-relaxed mt-1">
                                Personal portfolio and blog. writing about Rust, Distributed Systems, and the future of local-first software.
                            </div>
                         </div>

                         {/* Result 3: GitHub (Filler) */}
                         <div className="mb-6 max-w-xl opacity-60">
                            <div className="group cursor-pointer">
                                <div className="text-sm text-[#202124] mb-1 flex items-center gap-1">
                                    <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-[10px]">GH</div>
                                    <div className="flex flex-col leading-none">
                                        <span className="text-[12px]">GitHub</span>
                                        <span className="text-[10px] text-gray-500">https://github.com › alex-chen-rust</span>
                                    </div>
                                </div>
                                <div className="text-xl text-[#1a0dab] group-hover:underline font-medium cursor-pointer">
                                    alex-chen-rust (Alex Chen) · GitHub
                                </div>
                            </div>
                            <div className="text-sm text-[#4d5156] leading-relaxed mt-1">
                                alex-chen-rust has 42 repositories available. Follow their code on GitHub.
                            </div>
                         </div>
                    </div>
                )}

                {/* 3. LINKEDIN PROFILE */}
                {step >= STEPS.SHOW_PROFILE && (
                    <div className="h-full bg-[#F3F2EF] p-4 overflow-hidden">
                        <div className="bg-white rounded-lg shadow-sm border border-gray-300 overflow-hidden max-w-2xl mx-auto">
                            <div className="h-20 bg-[#A0B4B7] relative">
                                <div className="absolute -bottom-8 left-4 w-20 h-20 rounded-full border-4 border-white bg-gray-200" />
                            </div>
                            <div className="pt-10 px-4 pb-4">
                                <h1 className="text-lg font-bold text-gray-900">Alex Chen</h1>
                                <p className="text-xs text-gray-600">Senior Systems Engineer | Rust | High-Scale Infrastructure</p>
                                <div className="flex gap-2 mt-2 text-[10px] text-gray-500">
                                    <span className="flex items-center gap-1"><Briefcase size={10}/> Ex-Netflix</span>
                                    <span className="flex items-center gap-1"><MapPin size={10}/> San Francisco</span>
                                </div>
                                <div className="mt-3 flex gap-2">
                                    <div className="bg-[#0a66c2] text-white px-3 py-1 rounded-full text-xs font-bold">Connect</div>
                                    <div className="border border-gray-400 px-3 py-1 rounded-full text-xs font-bold text-gray-600">Message</div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* LAYER 2: ENGRAM APP */}
      <AnimatePresence>
        {step >= STEPS.CLICK_DOCK && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="absolute w-[90%] h-[80%] bg-white rounded-xl shadow-2xl flex flex-col z-30 overflow-hidden border border-gray-200"
            style={{ top: "8%" }}
          >
             
            <div className="h-10 bg-white border-b border-gray-200 flex items-center px-4 justify-between">
                <div className="flex space-x-2 opacity-50"><div className="w-3 h-3 rounded-full bg-gray-300"/><div className="w-3 h-3 rounded-full bg-gray-300"/><div className="w-3 h-3 rounded-full bg-gray-300"/></div>
                <div className="text-xs font-mono text-gray-400 flex items-center gap-2"><ShieldCheck size={12} className="text-green-600" /> engram.local</div>
                <div className="w-16"/>
            </div>

            
            <div className="flex-1 p-6 flex flex-col justify-end space-y-4">
                 
                 {step > STEPS.APP_SEND && (
                    <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="self-end bg-[#1a1a1a] text-white px-4 py-2 rounded-2xl rounded-tr-sm text-sm"
                    >
                        {APP_QUERY}
                    </motion.div>
                 )}

                 
                 {step >= STEPS.APP_RESPONSE && (
                    <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="self-start bg-white border border-gray-200 p-4 rounded-xl rounded-tl-sm text-sm w-full shadow-sm"
                    >
                        <div className="flex items-center gap-2 text-[#F08787] font-bold text-xs mb-2 uppercase tracking-wider">
                            <Bot size={12} /> Candidate Screening
                        </div>
                        <p className="mb-2 text-gray-600">Matched "Alex Chen" against <span className="font-mono bg-gray-100 px-1 rounded">hiring_reqs.md</span>.</p>
                        <div className="bg-green-50 p-2 rounded border border-green-100 flex gap-2 items-center">
                            <CheckCircle2 size={14} className="text-green-600" />
                            <div className="text-xs font-bold text-green-700">92% Match: Rust & Infra</div>
                        </div>
                    </motion.div>
                 )}
            </div>

            
            <div className="h-14 border-t border-gray-100 bg-white flex items-center px-4 gap-2">
                <div className="flex-1 h-9 bg-gray-50 rounded-lg flex items-center px-3 text-sm text-gray-800">
                    {step >= STEPS.APP_TYPING && step <= STEPS.APP_SEND ? appValue : step > STEPS.APP_SEND ? APP_QUERY : ""}
                    {step === STEPS.APP_TYPING && <span className="w-0.5 h-4 bg-[#F08787] animate-pulse ml-0.5"/>}
                </div>
                 <motion.div 
                  animate={{ scale: step === STEPS.APP_SEND ? 0.9 : 1 }}
                  className="p-2 bg-[#F08787] text-white rounded-md"
                >
                    <Send size={14} />
                    </motion.div>
                </div>
          </motion.div>
        )}
      </AnimatePresence>

      
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 bg-white/20 backdrop-blur-xl border border-white/20 rounded-2xl flex items-center gap-4 shadow-2xl z-40">
          <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center text-white shadow-lg"><Globe size={20} /></div>
          <div className="w-px h-8 bg-white/20 mx-1" />
          <motion.div 
            animate={{ scale: step === STEPS.CLICK_DOCK ? 0.8 : 1 }}
            className="w-10 h-10 bg-[#1a1a1a] rounded-xl flex items-center justify-center text-[#F08787] shadow-lg border border-gray-600"
          >
             <Disc size={20} />
          </motion.div>
      </div>

      
      <motion.div
        className="absolute z-50 pointer-events-none will-change-transform"
        style={{ filter: "drop-shadow(0 4px 6px rgba(0,0,0,0.15))" }}
        initial={{ left: "50%", top: "60%" }}
        animate={{ left: cursor.left, top: cursor.top, scale: cursor.scale || 1 }}
        transition={{ type: "tween", ease: "easeInOut", duration: 0.8 }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M3 3L10.07 19.97L12.58 12.58L19.97 10.07L3 3Z" fill="#1a1a1a" stroke="white" strokeWidth="2"/></svg>
      </motion.div>

    </div>
  );
}