import React, { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Float } from '@react-three/drei';
import * as THREE from 'three';
import { useStore } from '../../store/useStore';

interface RiskTerrainProps {
  scenario?: 'base' | 'adverse_credit' | 'high_prepayment';
  onSelectSegment?: (creditBand: string, vintage: string) => void;
}

const CREDIT_BANDS = ['<620', '620-660', '660-700', '700-740', '740-780', '780+'];
const VINTAGES = ['2020-Q1', '2020-Q3', '2021-Q1', '2021-Q3', '2022-Q1', '2022-Q3'];

// Base hazard matrix by credit band (rows) x vintage (cols)
const BASE_HAZARDS = [
  [0.28, 0.32, 0.35, 0.42, 0.48, 0.52], // <620
  [0.18, 0.22, 0.25, 0.30, 0.34, 0.38], // 620-660
  [0.10, 0.12, 0.15, 0.18, 0.21, 0.24], // 660-700
  [0.05, 0.07, 0.08, 0.10, 0.12, 0.14], // 700-740
  [0.02, 0.03, 0.04, 0.05, 0.06, 0.07], // 740-780
  [0.01, 0.01, 0.02, 0.02, 0.03, 0.04], // 780+
];

function DeformedMesh({ scenario = 'base', onSelectSegment }: RiskTerrainProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hoveredPos, setHoveredPos] = useState<{ x: number; y: number } | null>(null);

  const scenarioMultiplier = useMemo(() => {
    if (scenario === 'adverse_credit') return 1.75;
    if (scenario === 'high_prepayment') return 0.85;
    return 1.0;
  }, [scenario]);

  const targetHeights = useMemo(() => {
    const heights = [];
    for (let r = 0; r < CREDIT_BANDS.length; r++) {
      for (let c = 0; c < VINTAGES.length; c++) {
        heights.push(BASE_HAZARDS[r][c] * scenarioMultiplier * 3.5);
      }
    }
    return heights;
  }, [scenarioMultiplier]);

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(8, 8, VINTAGES.length - 1, CREDIT_BANDS.length - 1);
    geo.rotateX(-Math.PI / 2);
    return geo;
  }, []);

  // Smooth lerp of vertex heights
  useFrame((_, delta) => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position;
    const colors = [];
    const colorTeal = new THREE.Color('#3E8E82');
    const colorAmber = new THREE.Color('#D9A441');
    const colorRust = new THREE.Color('#B4482E');

    for (let i = 0; i < posAttr.count; i++) {
      const targetY = targetHeights[i] || 0;
      const currentY = posAttr.getY(i);
      const newY = THREE.MathUtils.lerp(currentY, targetY, Math.min(delta * 5, 1));
      posAttr.setY(i, newY);

      // Color mapping based on height
      const t = Math.min(Math.max(newY / 2.5, 0), 1);
      const c = new THREE.Color();
      if (t < 0.4) {
        c.lerpColors(colorTeal, colorAmber, t / 0.4);
      } else {
        c.lerpColors(colorAmber, colorRust, (t - 0.4) / 0.6);
      }
      colors.push(c.r, c.g, c.b);
    }

    meshRef.current.geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    posAttr.needsUpdate = true;
    meshRef.current.geometry.computeVertexNormals();

    // Gentle idle rotation
    meshRef.current.rotation.y += delta * 0.03;
  });

  return (
    <group>
      <mesh
        ref={meshRef}
        geometry={geometry}
        onClick={(e) => {
          e.stopPropagation();
          if (e.point && onSelectSegment) {
            const normalizedX = Math.floor(((e.point.x + 4) / 8) * VINTAGES.length);
            const normalizedZ = Math.floor(((e.point.z + 4) / 8) * CREDIT_BANDS.length);
            const vIdx = Math.min(Math.max(normalizedX, 0), VINTAGES.length - 1);
            const cIdx = Math.min(Math.max(normalizedZ, 0), CREDIT_BANDS.length - 1);
            onSelectSegment(CREDIT_BANDS[cIdx], VINTAGES[vIdx]);
          }
        }}
      >
        <meshStandardMaterial
          vertexColors
          wireframe={false}
          roughness={0.4}
          metalness={0.2}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Wireframe overlay */}
      <mesh geometry={geometry} position={[0, 0.02, 0]}>
        <meshBasicMaterial wireframe color="#C4903F" transparent opacity={0.35} />
      </mesh>

      {/* Grid Floor */}
      <gridHelper args={[10, 10, '#C4903F', '#1B2130']} position={[0, -0.1, 0]} />
    </group>
  );
}

export const RiskTerrain: React.FC<RiskTerrainProps> = ({ scenario = 'base', onSelectSegment }) => {
  return (
    <div className="w-full h-full min-h-[420px] rounded-lg overflow-hidden relative bg-ink-950/80 border border-brass-500/30">
      <div className="absolute top-4 left-4 z-10 pointer-events-none">
        <span className="engraved-label block text-brass-400">3D Terrain Telemetry</span>
        <h4 className="font-display text-base text-paper-100 font-medium">Default Risk Elevation Topography</h4>
        <p className="text-xs text-paper-300 font-mono mt-0.5">X: Vintage Cohort | Z: FICO Credit Band | Y: Hazard</p>
      </div>

      <div className="absolute bottom-4 right-4 z-10 flex items-center gap-2 text-xs font-mono bg-ink-900/90 px-3 py-1.5 rounded border border-brass-500/20">
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-signal-teal"></span> Low</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-signal-amber"></span> Moderate</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-signal-rust"></span> High</span>
      </div>

      <Canvas camera={{ position: [7, 6, 7], fov: 45 }}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[10, 15, 10]} intensity={1.2} color="#F4EFE4" />
        <pointLight position={[-10, 5, -10]} intensity={0.8} color="#C4903F" />
        <DeformedMesh scenario={scenario} onSelectSegment={onSelectSegment} />
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          maxPolarAngle={Math.PI / 2.1}
          minDistance={4}
          maxDistance={18}
        />
      </Canvas>
    </div>
  );
};
