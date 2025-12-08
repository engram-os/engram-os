"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FileText, 
  Send, 
  ShieldCheck, 
  Cpu, 
  Bot, 
  Database,
  Clock,
  LayoutGrid,
  Wifi,
  Download,
  AppWindow,
  Cloud,
  Users,
  Trash2,
  Disc,
  FileSpreadsheet

} from "lucide-react";

const STEPS = {
  IDLE: 0,
  MOVE_TO_FOLDER: 1,
  CLICK_FOLDER: 2,
  MOVE_TO_FILE: 3, 
  SELECT_FILE: 4,  
  PROCESSING: 5,   
  MOVE_TO_CHAT: 6, 
  TYPING: 7,
  MOVE_TO_SEND: 8, 
  CLICK_SEND: 9,   
  RESPONSE: 10,
};

const TYPING_TEXT = "Show me the approved salary bands for Engineering.";

const FILES = [
  { name: "hiring_reqs.md", type: "md", size: "12mb" },
  { name: "budget_2025.xlsx", type: "xlsx", size: "2.4mb" },
  { name: "q1_goals.pdf", type: "pdf", size: "450kb" }
];

export default function ProductSimulation() {
  const [step, setStep] = useState(STEPS.IDLE);
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    let isMounted = true;
    const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    const runSimulation = async () => {
      while (isMounted) {
        setStep(STEPS.IDLE);
        setDisplayedText("");
        await wait(1000);


        if (!isMounted) break;
        setStep(STEPS.MOVE_TO_FOLDER);
        await wait(1500);


        if (!isMounted) break;
        setStep(STEPS.CLICK_FOLDER);
        await wait(800); 


        if (!isMounted) break;
        setStep(STEPS.MOVE_TO_FILE);
        await wait(1500); 


        if (!isMounted) break;
        setStep(STEPS.SELECT_FILE); 
        await wait(600); 


        if (!isMounted) break;
        setStep(STEPS.PROCESSING);
        await wait(2000);


        if (!isMounted) break;
        setStep(STEPS.MOVE_TO_CHAT);
        await wait(1500); 


        if (!isMounted) break;
        setStep(STEPS.TYPING);
        for (let i = 0; i <= TYPING_TEXT.length; i++) {
          if (!isMounted) break;
          setDisplayedText(TYPING_TEXT.slice(0, i));
          await wait(40); 
        }
        await wait(500);


        if (!isMounted) break;
        setStep(STEPS.MOVE_TO_SEND);
        await wait(1500);


        if (!isMounted) break;
        setStep(STEPS.CLICK_SEND);
        await wait(400); 


        if (!isMounted) break;
        setStep(STEPS.RESPONSE);
        await wait(5000); 
      }
    };

    runSimulation();
    return () => { isMounted = false; };
  }, []);

  const isChatting = step >= STEPS.PROCESSING;

  const isMessageSent = step >= STEPS.CLICK_SEND;

 
  const getCursorPos = () => {
    switch(step) {
      case STEPS.IDLE: return { left: "90%", top: "90%" };
      case STEPS.MOVE_TO_FOLDER: return { left: "8%", top: "51%" }; 
      case STEPS.CLICK_FOLDER: return { left: "8%", top: "51%", scale: 0.9 }; 
      case STEPS.MOVE_TO_FILE: return { left: "63%", top: "58%" }; 
      case STEPS.SELECT_FILE: return { left: "63%", top: "58%", scale: 0.9 }; 
      case STEPS.PROCESSING: return { left: "63%", top: "58%" };
      case STEPS.MOVE_TO_CHAT: return { left: "68%", top: "92%" }; 
      case STEPS.TYPING: return { left: "68%", top: "92%" };
      case STEPS.MOVE_TO_SEND: return { right: "5%", top: "92%" };
      case STEPS.CLICK_SEND: return { right: "5%", top: "92%", scale: 0.9 };
      case STEPS.RESPONSE: return { left: "90%", top: "90%" }; 
      default: return { left: "90%", top: "90%" };
    }
  };

  const cursorPos = getCursorPos();

  return (
    <div className="relative w-full max-w-4xl mx-auto aspect-[16/10] bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden font-sans select-none flex flex-col">
      

      <div className="h-10 bg-gray-50 border-b border-gray-200 flex items-center px-4 justify-between z-20 shrink-0">
        <div className="flex space-x-2">
          <div className="w-3 h-3 rounded-full bg-[#FF5F56] border border-[#E0443E]" />
          <div className="w-3 h-3 rounded-full bg-[#FFBD2E] border border-[#DEA123]" />
          <div className="w-3 h-3 rounded-full bg-[#27C93F] border border-[#1AAB29]" />
        </div>
        <div className="text-xs font-mono text-gray-400 flex items-center gap-2">
          <ShieldCheck size={12} className="text-green-600" />
          <span>engram.local</span>
        </div>
        <div className="w-16" /> 
      </div>

      <div className="flex flex-1 overflow-hidden relative">
        

        <div className="w-48 bg-[#F5F5F5]/80 backdrop-blur-xl border-r border-gray-200 pt-3 pb-3 hidden md:flex flex-col z-10 text-[11px] font-medium text-gray-500 overflow-y-auto">
            <SidebarItem icon={Clock} label="Recents" />
            <SidebarItem icon={Users} label="Shared" />
          
          <div className="mb-4">
            <div className="px-3 mb-1 text-gray-400 text-[10px] font-bold">Favorites</div>

            <SidebarItem icon={LayoutGrid} label="Desktop" active={step < STEPS.CLICK_FOLDER} />
            <SidebarItem icon={AppWindow} label="Applications" />
            <SidebarItem icon={FileText} label="Documents" />
            <SidebarItem icon={Download} label="Downloads" />
          </div>

          <div className="mb-4">
            <div className="px-3 mb-1 text-gray-400 text-[10px] font-bold">Locations</div>
            <SidebarItem icon={Cloud} label="iCloud Drive" />
            
            <SidebarItem 
              icon={Disc} 
              label="Engram Local" 
              active={step >= STEPS.CLICK_FOLDER} 
            />
            
            <SidebarItem icon={Wifi} label="AirDrop" />
            <SidebarItem icon={Trash2} label="Trash" />
          </div>

          <div className="mt-auto">
            <div className="px-3 mb-1 text-gray-400 text-[10px] font-bold">Tags</div>
            <div className="flex items-center gap-2 px-3 py-1 hover:bg-black/5 cursor-default transition">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500" /> Red
            </div>
            <div className="flex items-center gap-2 px-3 py-1 hover:bg-black/5 cursor-default transition">
              <div className="w-2.5 h-2.5 rounded-full bg-orange-500" /> Orange
            </div>
            <div className="flex items-center gap-2 px-3 py-1 hover:bg-black/5 cursor-default transition">
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" /> Yellow
            </div>
            <div className="flex items-center gap-2 px-3 py-1 hover:bg-black/5 cursor-default transition">
              <div className="w-2.5 h-2.5 rounded-full bg-green-500" /> Green
            </div>
            <div className="flex items-center gap-2 px-3 py-1 hover:bg-black/5 cursor-default transition">
              <div className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Blue
            </div>
            <div className="flex items-center gap-2 px-3 py-1 hover:bg-black/5 cursor-default transition">
              <div className="w-2.5 h-2.5 rounded-full bg-purple-500" /> Purple
            </div>
            <div className="flex items-center gap-2 px-3 py-1 hover:bg-black/5 cursor-default transition">
              <div className="w-2.5 h-2.5 rounded-full bg-pink-500" /> Pink
            </div>
          </div>
        </div>


        <div className="flex-1 flex flex-col relative bg-white z-0">
          
          <div className="flex-1 p-8 relative flex flex-col justify-center">
            

            <AnimatePresence mode="wait">
            {!isChatting && (
               <div className="absolute inset-0 p-8 flex flex-col justify-center items-center"
               >

                 {step >= STEPS.CLICK_FOLDER ? (
                   <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="w-full flex flex-col items-center"
                   >
                      <div className="text-center mb-10">
                        <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                          <Database className="w-6 h-6 text-[#F08787]" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-800">Select a Memory</h3>
                        <p className="text-sm text-gray-500 mt-1">Choose a local file to ingest.</p>
                      </div>

                      <div className="flex gap-4 w-full max-w-xl justify-center">
                        {FILES.map((file, idx) => {
                          const isTarget = idx === 1;
                          const isSelected = isTarget && step === STEPS.SELECT_FILE;
                          return (
                            <motion.div 
                              key={file.name}
                              animate={{
                                borderColor: isSelected ? "#F08787" : "#e5e7eb",
                                backgroundColor: isSelected ? "#FFF5F5" : "#ffffff",
                                scale: isSelected ? 0.95 : 1,
                                y: isSelected ? 2 : 0,
                              }}
                              className="flex-1 p-4 h-32 rounded-xl border-2 transition-all flex flex-col items-center justify-center text-center gap-2 bg-white shadow-sm"
                            >
                              <FileText size={28} className={isSelected ? "text-[#F08787]" : "text-gray-300"} />
                              <div className="w-full">
                                <div className="text-xs font-semibold text-gray-700 truncate">{file.name}</div>
                                <div className="text-[10px] text-gray-400 mt-1">{file.size}</div>
                              </div>
                            </motion.div>
                          )
                        })}
                        </div>
                   </motion.div>
                 ) : (

                   <div className="text-gray-300 flex flex-col items-center">

                     <Download size={48} className="mb-4 opacity-20" />
                     <p className="text-sm">Desktop Empty</p>
                   </div>
                 )}
               </div>
            )}
            </AnimatePresence>



            <AnimatePresence>
            {isChatting && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex-1 space-y-6 pt-4 max-w-2xl mx-auto w-full"
              >

                 <AnimatePresence>
                  {step === STEPS.PROCESSING && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className="flex justify-center mb-8"
                    >
                      <div className="bg-gray-900 text-white text-xs py-2 px-4 rounded-full flex items-center gap-3 shadow-xl">
                        <Cpu size={14} className="animate-spin text-[#F08787]" />
                        <span className="font-medium tracking-wide">PARSING :: budget_2025.xlsx</span>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>


                <div className="space-y-6">

                  <AnimatePresence>
                    {isMessageSent && (
                      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end">
                        <div className="max-w-[80%] bg-[#1a1a1a] text-white p-3 px-4 rounded-2xl rounded-tr-none shadow-sm">
                          <p className="text-sm">{TYPING_TEXT}</p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>


                  <AnimatePresence>
                    {step >= STEPS.RESPONSE && (
                      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex justify-start">
                        <div className="max-w-[95%] bg-white border border-gray-100 text-gray-800 p-4 rounded-2xl rounded-tl-none shadow-sm">
                          <div className="flex items-center gap-2 mb-3 text-[#F08787] text-xs font-bold uppercase tracking-wider">
                            <Bot size={12} /> Engram
                          </div>
                          <div className="space-y-3 text-sm leading-relaxed text-gray-600">

                            <p>Here are the approved FY25 bands from <span className="font-mono text-xs bg-green-50 text-green-700 px-1 py-0.5 rounded border border-green-100">budget_2025.xlsx</span>:</p>

                            <div className="border rounded-lg overflow-hidden text-xs">

                                <div className="grid grid-cols-3 bg-gray-50 border-b p-2 font-bold text-gray-500 uppercase tracking-wider">

                                    <div className="col-span-2">Role</div>

                                    <div>Allocation</div>

                                </div>

                                <div className="grid grid-cols-3 p-2 border-b last:border-0 hover:bg-gray-50">

                                    <div className="col-span-2 font-medium text-gray-900">Senior Systems Eng.</div>

                                    <div className="text-green-600 font-mono">$180k - $220k</div>

                                </div>

                                <div className="grid grid-cols-3 p-2 border-b last:border-0 hover:bg-gray-50">

                                    <div className="col-span-2 font-medium text-gray-900">Backend Engineer</div>

                                    <div className="text-green-600 font-mono">$140k - $170k</div>

                                </div>

                                <div className="grid grid-cols-3 p-2 border-b last:border-0 hover:bg-gray-50">

                                    <div className="col-span-2 font-medium text-gray-900">DevOps Lead</div>

                                    <div className="text-green-600 font-mono">$190k - $240k</div>

                                </div>

                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
            </AnimatePresence>
          </div>

          <motion.div 
            animate={{ opacity: isChatting ? 1 : 0, y: isChatting ? 0 : 20 }}
            className="p-4 border-t border-gray-100 bg-white z-10"
          >
            <div className="max-w-2xl mx-auto relative">
              <div className="w-full h-11 bg-gray-50 border border-gray-200 rounded-xl flex items-center px-4 text-sm text-gray-900">

                {!isMessageSent && step >= STEPS.TYPING ? displayedText : ""}
                {!isMessageSent && step === STEPS.TYPING && <span className="w-0.5 h-4 bg-[#F08787] animate-pulse ml-0.5"/>}
              </div>
              <motion.div 
                className="absolute right-1.5 top-1.5 p-2 bg-[#F08787] text-white rounded-lg shadow-sm"
                animate={{ scale: step === STEPS.CLICK_SEND ? 0.9 : 1 }}
              >
                <Send size={14} />
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>
      

      <motion.div
            className="absolute z-50 pointer-events-none will-change-transform"
            style={{ filter: "drop-shadow(0 4px 6px rgba(0,0,0,0.15))" }}
            initial={{ left: "95%", top: "95%" }}
            animate={{
              left: cursorPos.left,
              top: cursorPos.top,
              scale: cursorPos.scale || 1
            }}
            transition={{
              type: "tween",
              ease: "easeInOut",
              duration: 1.2 
            }}
          >
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 3L10.07 19.97L12.58 12.58L19.97 10.07L3 3Z" fill="#1a1a1a" stroke="white" strokeWidth="2"/>
            </svg>
      </motion.div>

    </div>
  );
}


function SidebarItem({ icon: Icon, label, active = false }: { icon: any, label: string, active?: boolean }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-1 rounded cursor-default transition ${active ? 'bg-[#E5E5E5] text-gray-900 font-semibold' : 'hover:bg-black/5'}`}>
      <Icon size={14} className={active ? 'text-gray-900' : 'text-gray-500'} />
      {label}
    </div>
  )
}