import React, { useEffect, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Float } from '@react-three/drei';
import * as THREE from 'three';
import { useStore } from '../store/useStore';
import { api } from '../api/client';
import { 
  Compass, 
  Database, 
  Target, 
  GitBranch, 
  AlertTriangle, 
  Layers, 
  Sparkles, 
  Bot, 
  ArrowRight,
  TrendingUp,
  Cpu,
  Layers2
} from 'lucide-react';

function Astrolabe() {
  const outerRingRef = React.useRef<THREE.Mesh>(null);
  const midRingRef = React.useRef<THREE.Mesh>(null);
  const innerSphereRef = React.useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    const elapsed = clock.getElapsedTime();
    if (outerRingRef.current) {
      outerRingRef.current.rotation.x = elapsed * 0.15;
      outerRingRef.current.rotation.y = elapsed * 0.1;
    }
    if (midRingRef.current) {
      midRingRef.current.rotation.y = -elapsed * 0.2;
      midRingRef.current.rotation.z = elapsed * 0.15;
    }
    if (innerSphereRef.current) {
      innerSphereRef.current.rotation.y = elapsed * 0.3;
    }
  });

  return (
    <group scale={1.3}>
      {/* Outer Brass Ring */}
      <mesh ref={outerRingRef}>
        <torusGeometry args={[2.5, 0.04, 8, 64]} />
        <meshStandardMaterial color="#D9A441" roughness={0.1} metalness={0.9} wireframe />
      </mesh>

      {/* Mid Accent Ring */}
      <mesh ref={midRingRef}>
        <torusGeometry args={[2.0, 0.03, 8, 64]} />
        <meshStandardMaterial color="#B4482E" roughness={0.2} metalness={0.8} wireframe />
      </mesh>

      {/* Inner Sphere */}
      <mesh ref={innerSphereRef}>
        <sphereGeometry args={[1.2, 16, 16]} />
        <meshStandardMaterial color="#3E8E82" roughness={0.3} metalness={0.7} wireframe />
      </mesh>

      {/* Ambient Grid Floor */}
      <gridHelper args={[8, 16, '#D9A441', '#2C2B2A']} position={[0, -2.5, 0]} />
    </group>
  );
}

export const Landing: React.FC = () => {
  const { setActiveTab } = useStore();
  const [stats, setStats] = useState({
    totalRecords: '576,614',
    staticRows: '15,000',
    dqScore: '60.9%',
    modelsCount: '7'
  });

  useEffect(() => {
    // Load live statistics from backend summary report
    api.getDQSummary().then((res) => {
      const shape = res.data?.dataset_shape;
      if (shape) {
        const total = (shape.train_rows || 0) + (shape.test_rows || 0);
        setStats((prev) => ({
          ...prev,
          totalRecords: total > 0 ? total.toLocaleString() : prev.totalRecords,
          staticRows: shape.static_rows ? shape.static_rows.toLocaleString() : prev.staticRows,
          dqScore: res.data?.data_quality_score ? `${res.data.data_quality_score}%` : prev.dqScore
        }));
      }
    }).catch(() => {});

    api.getHealth().then((res) => {
      if (res.data?.models_loaded) {
        setStats((prev) => ({
          ...prev,
          modelsCount: String(res.data.models_loaded)
        }));
      }
    }).catch(() => {});
  }, []);

  const features = [
    { name: 'Loan Performance Prediction', desc: 'Non-LLM LightGBM predictive models mapping 3-month/6-month delinquency and default risks.', icon: Target },
    { name: 'Survival & Hazards Modeling', desc: 'Cox Proportional Hazards and Kaplan-Meier estimation for multi-period default/prepayment scenarios.', icon: GitBranch },
    { name: 'Anomaly Detection Triage', desc: 'Blended 60% IsolationForest and 40% PyTorch Autoencoder anomalies lookup.', icon: AlertTriangle },
    { name: 'Monte Carlo Stress Scenarios', desc: 'Monte Carlo quarterly simulation across base, adverse credit, and prepayment shock scenarios.', icon: Layers },
    { name: 'SHAP Explainability', desc: 'Calibrated tree-explainer local and global SHAP attribution mapping risk drivers.', icon: Sparkles },
    { name: 'RAG-Grounded AI Copilot', desc: 'ChromaDB vector database grounding with governed prompts and safety disclaimers.', icon: Bot }
  ];

  return (
    <div className="min-h-screen bg-ink-950 text-paper-100 flex flex-col font-body selection:bg-brass-500 selection:text-ink-950">
      
      {/* Landing Main Header / Hero Panel */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-12 flex flex-col lg:grid lg:grid-cols-2 gap-12 items-center">
        
        {/* Left Side: Descriptions & Details */}
        <div className="space-y-8 flex flex-col justify-center">
          
          <div className="space-y-4">
            <span className="engraved-label tracking-[0.2em] text-brass-400">Task 8 Observatory Release</span>
            <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-paper-100 leading-tight">
              THE OBSERVATORY
            </h1>
            <p className="text-base md:text-lg text-paper-300 max-w-xl font-body leading-relaxed">
              A premium, time-aware risk analytics platform for loan portfolio reviewers and credit analysts. 
              Engineered with a robust, non-LLM machine learning core, wrapped in a governed RAG-grounded AI copilot feedback layer.
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-wrap gap-4 pt-2">
            <button
              onClick={() => setActiveTab('overview')}
              className="bg-brass-500 hover:bg-brass-400 text-ink-950 font-mono font-bold text-sm px-8 py-4 rounded shadow-brass-md transition-all flex items-center gap-2 group"
            >
              Launch Observatory
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </button>
            <a
              href="#features"
              className="border border-brass-500/30 hover:border-brass-400 text-brass-400 hover:text-paper-100 font-mono font-bold text-sm px-6 py-4 rounded transition-all"
            >
              View Specifications
            </a>
          </div>

          {/* Live Stats Strip */}
          <div className="grid grid-cols-3 gap-6 pt-6 border-t border-brass-500/10 max-w-lg">
            <div>
              <span className="text-[10px] font-mono text-brass-400 block uppercase tracking-wider">Records Analyzed</span>
              <span className="font-display font-semibold text-2xl text-paper-100 mt-1 block">{stats.totalRecords}</span>
            </div>
            <div>
              <span className="text-[10px] font-mono text-brass-400 block uppercase tracking-wider">Calibrated Models</span>
              <span className="font-display font-semibold text-2xl text-paper-100 mt-1 block">{stats.modelsCount} Online</span>
            </div>
            <div>
              <span className="text-[10px] font-mono text-brass-400 block uppercase tracking-wider">Data Quality Score</span>
              <span className="font-display font-semibold text-2xl text-signal-teal mt-1 block">{stats.dqScore}</span>
            </div>
          </div>

        </div>

        {/* Right Side: Visual 3D Instrument */}
        <div className="w-full h-[400px] lg:h-[600px] relative rounded-lg border border-brass-500/15 bg-ink-950/60 shadow-inner flex items-center justify-center overflow-hidden">
          
          {/* Scientific Overlay Graticules */}
          <div className="absolute inset-0 pointer-events-none border border-brass-500/10 m-6 flex items-center justify-center">
            <div className="w-full h-[1px] bg-brass-500/10 absolute" />
            <div className="h-full w-[1px] bg-brass-500/10 absolute" />
            <div className="border border-brass-500/10 rounded-full w-48 h-48 absolute" />
            <div className="border border-brass-500/10 rounded-full w-96 h-96 absolute" />
          </div>

          <div className="absolute top-4 left-4 font-mono text-[9px] text-brass-400/60 uppercase tracking-widest">
            Observation Lens 0.1A // Astrolabe
          </div>
          
          <Canvas camera={{ position: [0, 0, 6], fov: 50 }}>
            <ambientLight intensity={0.4} />
            <pointLight position={[10, 10, 10]} intensity={1.5} color="#D9A441" />
            <pointLight position={[-10, -10, -10]} intensity={0.5} color="#3E8E82" />
            <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
              <Astrolabe />
            </Float>
            <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} />
          </Canvas>
        </div>

      </main>

      {/* Specifications / Features Grid */}
      <section id="features" className="border-t border-brass-500/20 bg-ink-950/60 py-16 px-6 md:px-12">
        <div className="max-w-7xl mx-auto space-y-12">
          
          <div className="text-center max-w-xl mx-auto space-y-3">
            <span className="engraved-label text-brass-400">Observatory Architecture</span>
            <h2 className="font-display text-3xl font-bold text-paper-100">
              Technical Specifications
            </h2>
            <p className="text-sm text-paper-300 leading-relaxed font-body">
              Engineered to enforce strict isolation of core analytical engines while supporting governed semantic assistant queries.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, idx) => {
              const Icon = f.icon;
              return (
                <div key={idx} className="observatory-panel p-6 space-y-4 hover:border-brass-500/35 transition-all">
                  <div className="flex items-center gap-3">
                    <span className="p-2 rounded bg-brass-500/10 text-brass-400 border border-brass-500/20">
                      <Icon className="w-5 h-5" />
                    </span>
                    <h3 className="font-display text-base font-semibold text-paper-100">{f.name}</h3>
                  </div>
                  <p className="text-xs text-paper-300 font-body leading-relaxed">{f.desc}</p>
                </div>
              );
            })}
          </div>

          <div className="text-center pt-6">
            <button
              onClick={() => setActiveTab('overview')}
              className="bg-brass-500/10 hover:bg-brass-500/20 text-brass-400 border border-brass-500/30 hover:border-brass-500/50 font-mono font-bold text-xs px-8 py-3 rounded transition-all"
            >
              Enter Analyst Dashboard
            </button>
          </div>

        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-brass-500/20 bg-ink-950 px-4 py-6 text-center font-mono text-xs text-paper-300">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Intain Campus FinTech Challenge 2026 — AI Track</span>
          <span className="text-brass-400">Grounded Non-LLM ML + RAG Assisted Workflow</span>
          <span>Status: Verified Runnable Prototype</span>
        </div>
      </footer>

    </div>
  );
};
