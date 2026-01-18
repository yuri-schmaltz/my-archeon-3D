
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stage, useGLTF, Grid } from "@react-three/drei";
import { Suspense } from "react";

function Model({ url }: { url: string }) {
    // Note: In a real implementation we might need to handle file protocols differently in production
    // or use loadAsync if invalid URL. For now assuming simple HTTP or convertFileSrc
    const { scene } = useGLTF(url);
    return <primitive object={scene} />;
}

export function Viewer3D({ modelUrl }: { modelUrl?: string }) {

    return (
        <div className="w-full h-full">
            <Canvas shadows camera={{ position: [0, 0, 4], fov: 50 }}>
                <color attach="background" args={["#1a1a1a"]} />
                <Suspense fallback={null}>
                    <Stage environment="city" intensity={0.6}>
                        {modelUrl ? (
                            <Model url={modelUrl} />
                        ) : (
                            <mesh>
                                <boxGeometry args={[1, 1, 1]} />
                                <meshStandardMaterial color="hotpink" wireframe />
                            </mesh>
                        )}
                    </Stage>
                    <Grid
                        renderOrder={-1}
                        position={[0, -0.5, 0]}
                        infiniteGrid
                        cellSize={0.5}
                        sectionSize={2.5}
                        fadeDistance={25}
                        sectionColor="#4d4d4d"
                        cellColor="#333333"
                    />
                </Suspense>
                <OrbitControls makeDefault autoRotate={!modelUrl} />
            </Canvas>

            {!modelUrl && (
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none text-white/50 text-sm">
                    Waiting for generation...
                </div>
            )}
        </div>
    );
}
