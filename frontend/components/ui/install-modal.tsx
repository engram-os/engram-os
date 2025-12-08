"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Copy, Check, ChevronRight } from "lucide-react";

interface InstallModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function InstallModal({ isOpen, onClose }: InstallModalProps) {
  if (typeof window !== "undefined") {
    if (isOpen) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "unset";
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100]"
          />

          
          <div className="fixed inset-0 flex items-center justify-center z-[101] p-4 pointer-events-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="bg-[#0A0A0A] w-full max-w-xl rounded-xl border border-[#27272a] shadow-2xl overflow-hidden pointer-events-auto flex flex-col"
            >
              
              <div className="flex items-center justify-between p-5 pb-0">
                <h2 className="text-lg font-bold text-white">
                  Get started with Engram
                </h2>
                <button 
                  onClick={onClose}
                  className="text-gray-500 hover:text-white transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              
              <div className="p-5 space-y-6">
                
                
                <div className="space-y-3">
                    <div className="text-sm text-gray-300 font-medium">
                        1. Open your terminal in your favorite IDE
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <IdeButton 
                          name="VS Code" 
                          url="https://code.visualstudio.com/" 
                          icon={<VSCodeIcon />} 
                        />
                        <IdeButton 
                          name="Cursor" 
                          url="https://cursor.sh/" 
                          icon={<CursorIcon />} 
                        />
                        <IdeButton 
                          name="IntelliJ" 
                          url="https://www.jetbrains.com/idea/" 
                          icon={<IntelliJIcon />} 
                        />
                        <IdeButton 
                          name="PyCharm" 
                          url="https://www.jetbrains.com/pycharm/" 
                          icon={<PyCharmIcon />} 
                        />
                    </div>
                </div>

                
                <Step 
                    number="2" 
                    title="Navigate to your project directory" 
                    command="cd /path/to/your-repo" 
                />

                
                <Step 
                    number="3" 
                    title="Install Engram" 
                    command="npm install -g engram" 
                />

                
                <Step 
                    number="4" 
                    title="Run Engram" 
                    command="engram" 
                />

              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}


function Step({ number, title, command }: { number: string, title: string, command: string }) {
    const [copied, setCopied] = useState(false);

    const copyToClipboard = () => {
        navigator.clipboard.writeText(command);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="space-y-3">
            <div className="text-sm text-gray-300 font-medium">
                {number}. {title}
            </div>
            <div className="group relative bg-[#18181b] border border-[#27272a] hover:border-gray-600 transition-colors rounded-lg p-3 flex items-center justify-between font-mono text-xs text-gray-300">
                <div className="flex items-center gap-3 truncate mr-4">
                    <ChevronRight size={14} className="text-[#F08787] shrink-0" />
                    <span className="truncate">{command}</span>
                </div>
                <button 
                    onClick={copyToClipboard}
                    className="text-gray-500 hover:text-white transition-colors p-1"
                >
                    {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                </button>
            </div>
        </div>
    )
}

function IdeButton({ name, url, icon }: { name: string, url: string, icon: React.ReactNode }) {
  return (
    <a 
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 px-3 py-2.5 bg-[#18181b] border border-[#27272a] hover:bg-[#27272a] hover:border-gray-500 transition-all rounded text-gray-300 text-xs font-medium select-none group"
    >
      <div className="shrink-0 w-5 h-5 p-0.5 flex items-center justify-center grayscale group-hover:grayscale-0 transition-all">
        {icon}
      </div>
      {name}
    </a>
  )
}


function VSCodeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="" xmlns="http://www.w3.org/2000/svg">
      <path d="M23.5 18L18.5 22L1 15L2.5 9L1 3L18.5 2L23.5 6L17.5 12L23.5 18Z" fill="#007ACC" stroke="none"/>
    </svg>
  )
}


function CursorIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#E0E0E0"/>
      <path d="M2 17L12 22L22 17" stroke="#E0E0E0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M2 7V17" stroke="#E0E0E0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M22 7V17" stroke="#E0E0E0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 12V22" stroke="#E0E0E0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}


function IntelliJIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="4" fill="url(#paint0_linear_intellij)"/>
      <path d="M7 7H17V17H7V7Z" fill="black" fillOpacity="0.2"/>
      <rect x="5" y="10" width="14" height="4" fill="white"/>
      <defs>
        <linearGradient id="paint0_linear_intellij" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
          <stop stopColor="#FE315D"/>
          <stop offset="0.5" stopColor="#F97A12"/>
          <stop offset="1" stopColor="#CB3AC1"/>
        </linearGradient>
      </defs>
    </svg>
  )
}


function PyCharmIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="4" fill="url(#paint0_linear_pycharm)"/>
      <path d="M6 6H18V18H6V6Z" fill="black" fillOpacity="0.3"/>
      <text x="5" y="17" fontSize="10" fontWeight="bold" fill="white" fontFamily="sans-serif">PC</text>
      <defs>
        <linearGradient id="paint0_linear_pycharm" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
          <stop stopColor="#21D789"/>
          <stop offset="1" stopColor="#07C3F2"/>
        </linearGradient>
      </defs>
    </svg>
  )
}