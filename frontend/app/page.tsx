import Link from "next/link"
import { Shield, Zap, Box, Scale, Stethoscope, FlaskConical, Github, FileText, ArrowRight } from "lucide-react"
import SimulationCarousel from "@/components/landing/simulation-carousel"
import ArchitectureGrid from "@/components/landing/architecture-grid"
import UseCases from "@/components/landing/use-cases"
import SiteFooter from "@/components/landing/site-footer"
import SiteHeader from "@/components/landing/site-header"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <SiteHeader />

      <main>
        <section className="container mx-auto px-6 py-24 md:py-32 text-center">

          <div className="relative z-10 max-w-4xl mx-auto text-center">
       
        <div className="inline-block mb-8 px-4 py-2 rounded-full border border-primary/50 text-primary text-sm font-medium">
          <span className="neon-purple">✦ The Future of Computing</span>
        </div>
          
          <div className="max-w-4xl mx-auto space-y-8">
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-foreground">
              Your AI, <span className="text-primary">On Your Device</span>
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto">
              Engram is a local-first AI Operating System for professionals who manage high-liability data. 
              All your data stays with you. Complete privacy. Complete control.
            </p>
            
            <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
              <Link 
                href="https://github.com/VS251/engram-os.git"
                className="inline-flex h-12 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <Github className="mr-2 h-4 w-4" /> View Source on GitHub
              </Link>
              <Link 
                href="/case-study"
                className="inline-flex h-12 items-center justify-center rounded-md border border-input bg-background px-8 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <FileText className="mr-2 h-4 w-4" /> Read Case Study
              </Link>
            </div>
          </div>

            <div className="mt-16">
              <SimulationCarousel />
            </div>
          </div>
        </section>

        
        <section id="features" className="bg-secondary/30 py-24">
          <div className="container mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold">Your Data is the Product. <span className="text-primary">Until Now.</span></h2>
            </div>
            
            <div className="grid md:grid-cols-3 gap-12">
              {/* Feature 1 */}
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="p-4 bg-background rounded-full shadow-sm">
                  <Shield className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-xl font-bold">Sovereign</h3>
                <p className="text-muted-foreground">
                  No API keys. No telemetry. No model training on your text. Your data physically cannot leave your machine.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="p-4 bg-background rounded-full shadow-sm">
                  <Zap className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-xl font-bold">Latency-Free</h3>
                <p className="text-muted-foreground">
                  Runs on local silicon using Docker. No network bottlenecks, no rate limits, and instant retrieval (&lt;200ms).
                </p>
              </div>

              {/* Feature 3 */}
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="p-4 bg-background rounded-full shadow-sm">
                  <Box className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-xl font-bold">Model Agnostic</h3>
                <p className="text-muted-foreground">
                  Don't get locked in. Swap the brain instantly: Run Llama 3, Mistral, Gemma, or DeepSeek with one config change.
                </p>
              </div>
            </div>
          </div>
        </section>

       {/* --- ARCHITECTURE SECTION --- */}
        <section id="architecture" className="bg-[#FAFAFA] py-24 border-y border-gray-200">
          <div className="container mx-auto px-6 mb-16 text-center">
             <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">Engineered for Zero Trust.</h2>
             <p className="text-gray-500 max-w-2xl mx-auto">
               No cloud vectors. No API keys. Just raw Python and Rust running on your local metal.
             </p>
          </div>
          
          <ArchitectureGrid />
        </section>

        <UseCases />

        <SiteFooter />
      </main>
    </div>
  )
}