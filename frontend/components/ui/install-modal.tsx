"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Rocket, Github } from "lucide-react";

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
              className="bg-[#0A0A0A] w-full max-w-md rounded-xl border border-[#27272a] shadow-2xl overflow-hidden pointer-events-auto flex flex-col"
            >
              <div className="flex items-center justify-end p-4 pb-0">
                <button 
                  onClick={onClose}
                  className="text-gray-500 hover:text-white transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="p-6pt-0 pb-8 text-center space-y-4">
                <div className="flex justify-center mb-4">
                    <div className="w-16 h-16 bg-[#18181b] rounded-full flex items-center justify-center border border-[#27272a]">
                        <Rocket size={32} className="text-[#F08787]" />
                    </div>
                </div>
                
                <h2 className="text-2xl font-bold text-white">
                  Shipping Soon
                </h2>
                
                <div className="space-y-2 text-sm text-gray-400 leading-relaxed">
                    <p>
                        We're wrapping up the final PRs and running integration tests on the public build.
                    </p>
                    <p>
                        The `v1.0.4-beta` release is just around the corner.
                    </p>
                </div>

                <div className="pt-4">
                    <a 
                      href="https://github.com/yourusername/engram" 
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-4 py-2.5 bg-white text-black rounded-lg font-medium text-sm hover:bg-[#F08787] hover:text-white transition-colors w-full justify-center"
                    >
                        <Github size={16} />
                        Star us for updates
                    </a>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}