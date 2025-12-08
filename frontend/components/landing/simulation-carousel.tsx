"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import ProductSimulation from "./product-simulation";
import HiringSimulation from "./hiring-simulation";
import JarvisSimulation from "./jarvis-simulation";
import { Database, Globe, Cpu } from "lucide-react";

const SLIDES = [
  {
    id: "files",
    label: "Local Vector Store", 
    icon: Database,
    component: ProductSimulation,
    color: "bg-[#F08787]",
    duration: 16000 
  },
  {
    id: "hiring",
    label: "Web Ingestion", 
    icon: Globe,
    component: HiringSimulation,
    color: "bg-[#0a66c2]",
    duration: 22000 
  },
  {
    id: "jarvis",
    label: "Autonomous Agent", 
    icon: Cpu,
    component: JarvisSimulation,
    color: "bg-purple-500",
    duration: 16000 
  }
];

export default function SimulationCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);


  useEffect(() => {
    const currentDuration = SLIDES[currentIndex].duration;
    
    const timer = setTimeout(() => {
      setCurrentIndex((prev) => (prev + 1) % SLIDES.length);
    }, currentDuration);

    return () => clearTimeout(timer);
  }, [currentIndex]);

  const ActiveComponent = SLIDES[currentIndex].component;

  return (
    <div className="w-full max-w-5xl mx-auto space-y-10">
      
      {/* 1. The Screen Area */}
      <div className="relative aspect-[16/10] bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <AnimatePresence mode="wait">
          {ActiveComponent && (
            <motion.div
              key={SLIDES[currentIndex].id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.5 }}
              className="w-full h-full"
            >
              <ActiveComponent />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 2. The "Expanding Pill" Navigation */}
      <div className="flex justify-center">
        <div className="flex items-center bg-white/50 backdrop-blur-md border border-gray-200 p-1.5 rounded-full shadow-sm gap-1.5">
          <LayoutGroup>
            {SLIDES.map((slide, idx) => {
              const isActive = idx === currentIndex;
              const Icon = slide.icon;
              
              return (
                <button
                  key={slide.id}
                  onClick={() => setCurrentIndex(idx)}
                  className="relative outline-none"
                >
                  <motion.div
                    layout
                    className={`
                      relative flex items-center gap-2 px-3 py-2 rounded-full transition-colors duration-300 overflow-hidden
                      ${isActive ? "bg-[#1a1a1a] text-white pr-4" : "hover:bg-gray-100 text-gray-400"}
                    `}
                  >
                    <motion.div layout className="relative z-10">
                      <Icon size={18} className={isActive ? slide.color.replace('bg-', 'text-') : "text-gray-400"} />
                    </motion.div>
                    
                    
                    <AnimatePresence mode="wait">
                        {isActive && (
                            <motion.span
                                initial={{ opacity: 0, width: 0 }}
                                animate={{ opacity: 1, width: "auto" }}
                                exit={{ opacity: 0, width: 0 }}
                                className="text-xs font-bold whitespace-nowrap z-10"
                            >
                                {slide.label}
                            </motion.span>
                        )}
                    </AnimatePresence>

                    
                    {isActive && (
                       <motion.div 
                         className="absolute bottom-0 left-0 h-full bg-white/10 z-0"
                         initial={{ width: "0%" }}
                         animate={{ width: "100%" }}
                         transition={{ duration: slide.duration / 1000, ease: "linear" }}
                       />
                    )}
                  </motion.div>
                </button>
              );
            })}
          </LayoutGroup>
        </div>
      </div>

    </div>
  );
}