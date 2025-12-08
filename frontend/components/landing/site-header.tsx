"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Download, Terminal, Check, Copy } from "lucide-react";
import InstallModal from "@/components/ui/install-modal";

export default function SiteHeader() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [installOpen, setInstallOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: "Features", href: "#features" },
    { name: "Architecture", href: "#architecture" },
    { name: "Use Cases", href: "#use-cases" },
  ];

  return (
    <>
      <header 
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 border-b ${
          isScrolled 
            ? "bg-white/80 backdrop-blur-xl border-gray-200/50 py-3 shadow-sm" 
            : "bg-transparent border-transparent py-6"
        }`}
      >
        <div className="container mx-auto px-6 flex items-center justify-between">
          
          
          <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight text-gray-900 group">
            <div className="w-8 h-8 bg-[#F08787] rounded-lg flex items-center justify-center text-white text-sm shadow-md group-hover:scale-105 transition-transform">
              E
            </div>
            <span>Engram</span>
          </Link>

          
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link 
                key={link.name} 
                href={link.href}
                className="text-sm font-medium text-gray-500 hover:text-[#1a1a1a] transition-colors relative group"
              >
                {link.name}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-[#F08787] transition-all duration-300 group-hover:w-full" />
              </Link>
            ))}
          </nav>

          
          <div className="hidden md:flex items-center gap-4">
            
            
            <CopyCommandButton command="npx engram@latest" />

            
            <div onClick={() => setInstallOpen(true)}>      
            <ShinyButton>
               <Download size={16} /> 
               <span>Get Early Access</span>
            </ShinyButton>
            </div>

          </div>

          
          <button 
            className="md:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </header>

      <InstallModal isOpen={installOpen} onClose={() => setInstallOpen(false)} />

      
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="fixed inset-x-0 top-[72px] z-40 bg-white border-b border-gray-200 overflow-hidden shadow-2xl md:hidden"
          >
            <nav className="flex flex-col p-6 gap-4">
              {navLinks.map((link) => (
                <Link 
                  key={link.name} 
                  href={link.href}
                  className="text-lg font-medium text-gray-900 py-2 border-b border-gray-100"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.name}
                </Link>
              ))}
              <div className="pt-4">
                 <CopyCommandButton command="npx engram@latest" />
              </div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}


function CopyCommandButton({ command }: { command: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(command);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <button 
            onClick={handleCopy}
            className="group relative flex items-center gap-3 px-4 py-2.5 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg text-xs font-mono text-gray-600 transition-all active:scale-95"
        >
            <div className="flex items-center gap-2">
                <Terminal size={14} className="text-gray-400 group-hover:text-[#F08787] transition-colors" />
                <span className="relative top-[1px]">
                    <span className="text-gray-400 select-none mr-2">$</span>
                    {command}
                </span>
            </div>
            
            <div className="w-px h-4 bg-gray-300 mx-1" />

            <div className="relative w-4 h-4">
                <AnimatePresence mode="wait">
                    {copied ? (
                        <motion.div
                            key="check"
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0, opacity: 0 }}
                            className="absolute inset-0 text-green-500"
                        >
                            <Check size={14} />
                        </motion.div>
                    ) : (
                        <motion.div
                            key="copy"
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0, opacity: 0 }}
                            className="absolute inset-0 text-gray-400 group-hover:text-black"
                        >
                            <Copy size={14} />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
            
            
            <AnimatePresence>
                {copied && (
                    <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-black text-white text-[10px] px-2 py-1 rounded shadow-lg whitespace-nowrap"
                    >
                        Copied to clipboard!
                    </motion.div>
                )}
            </AnimatePresence>
        </button>
    );
}


function ShinyButton({ children }: { children: React.ReactNode }) {
    return (
        <button className="relative inline-flex h-10 overflow-hidden rounded-lg p-[1px] focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 focus:ring-offset-gray-50">
            <span className="absolute inset-[-1000%] animate-[spin_3s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#E2CBFF_0%,#393BB2_50%,#E2CBFF_100%)]" />
            <span className="inline-flex h-full w-full cursor-pointer items-center justify-center gap-2 rounded-lg bg-[#1a1a1a] px-5 py-1 text-sm font-medium text-white backdrop-blur-3xl transition-all hover:bg-black/90">
                {children}
            </span>
        </button>
    );
}