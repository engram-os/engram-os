"use client";

import { motion } from "framer-motion";
import { 
  Scale, 
  Stethoscope, 
  FlaskConical, 
  Users, 
  Building2, 
  CheckCircle2 
} from "lucide-react";

const USE_CASES = [
  {
    id: "legal",
    title: "Legal Counsel",
    icon: Scale,
    description: "Ingest case files and discovery documents. Search for liability clauses across thousands of PDFs without breaking attorney-client privilege.",
    badge: "Privilege Intact",
    color: "bg-blue-500",
    lightColor: "bg-blue-50",
    textColor: "text-blue-600"
  },
  {
    id: "healthcare",
    title: "Healthcare",
    icon: Stethoscope,
    description: "Analyze patient notes and research papers locally. Data never leaves the machine, ensuring absolute compliance by definition.",
    badge: "HIPAA Compliant",
    color: "bg-emerald-500",
    lightColor: "bg-emerald-50",
    textColor: "text-emerald-600"
  },
  {
    id: "rnd",
    title: "R&D / IP",
    icon: FlaskConical,
    description: "Index proprietary codebases, chemical schematics, and trade secrets. Your Intellectual Property stays strictly on your hard drive.",
    badge: "IP Sovereign",
    color: "bg-purple-500",
    lightColor: "bg-purple-50",
    textColor: "text-purple-600"
  },
  {
    id: "hr",
    title: "Talent & HR",
    icon: Users,
    description: "Screen candidates against internal salary bands and sensitive roadmaps. Keep PII and compensation data completely off the cloud.",
    badge: "GDPR Safe",
    color: "bg-rose-500",
    lightColor: "bg-rose-50",
    textColor: "text-rose-600"
  },
  {
    id: "finance",
    title: "Finance & Gov",
    icon: Building2,
    description: "From M&A due diligence to public sector clearance. If it's too sensitive for standard AI tools, it belongs in Engram.",
    badge: "Zero Leaks",
    color: "bg-amber-500",
    lightColor: "bg-amber-50",
    textColor: "text-amber-600"
  }
];

export default function UseCases() {
  return (
    <section id="use-cases" className="py-24 bg-[#FFF0E6]">
      <div className="container mx-auto px-6">
        
        
        <div className="text-center mb-16 max-w-2xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-gray-900">
            When "The Cloud" Isn't an Option
          </h2>
          <p className="text-gray-600 text-lg">
            For professionals who manage high-liability data, privacy isn't a feature—it's a requirement.
          </p>
        </div>

        
        <div className="flex flex-wrap justify-center gap-8">
          {USE_CASES.map((item) => (
            <motion.div
              key={item.id}
              whileHover={{ y: -8 }}
              className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all duration-300 border border-transparent hover:border-gray-200 group w-full md:w-[calc(50%-1rem)] lg:w-[calc(33.333%-1.5rem)]"
            >
              
              <div className={`w-14 h-14 rounded-xl ${item.lightColor} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                <item.icon size={28} className={item.textColor} />
              </div>

              
              <div className="flex flex-col gap-2 mb-4">
                <h3 className="text-xl font-bold text-gray-900">{item.title}</h3>
                
                <div className="flex items-center gap-2">
                    <div className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5 ${item.lightColor} ${item.textColor}`}>
                        <ShieldCheckAnim /> 
                        {item.badge}
                    </div>
                </div>
              </div>

              <p className="text-gray-500 leading-relaxed text-sm">
                {item.description}
              </p>

              
              <div className="mt-8 h-1 w-full bg-gray-100 rounded-full overflow-hidden">
                <motion.div 
                    className={`h-full ${item.color}`}
                    initial={{ width: "0%" }}
                    whileHover={{ width: "100%" }}
                    transition={{ duration: 0.4 }}
                />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}


function ShieldCheckAnim() {
    return (
        <motion.svg 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="3" 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            className="w-3 h-3"
        >
            <motion.path 
                d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" 
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                transition={{ duration: 0.5 }}
            />
        </motion.svg>
    )
}