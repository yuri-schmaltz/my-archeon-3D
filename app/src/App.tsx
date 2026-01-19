import { useState, useEffect } from "react";
import "./App.css";
import { ArcheonClient } from "./lib/api";
import { AppLayout } from "./components/layout/AppLayout";
import { Viewer3D } from "./components/viewer/Viewer3D";
import { useJobManager } from "./lib/useJobManager";
import { Label } from "./components/ui/label";
import { Input } from "./components/ui/input";
import { Slider } from "./components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { ImageUpload } from "./components/ui/image-upload";
import { convertFileSrc } from "@tauri-apps/api/core";

import { SidecarManager } from "./lib/SidecarManager";

function App() {
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");

  // Job Parameters
  const [mode, setMode] = useState<"text_to_3d" | "image_to_3d">("text_to_3d");
  const [prompt, setPrompt] = useState("");
  const [negPrompt, setNegPrompt] = useState("blurry, low quality, distorted");
  const [imagePath, setImagePath] = useState<string | undefined>(undefined);

  const [steps, setSteps] = useState(30);
  const [guidance, setGuidance] = useState(5.5);
  const [seed, setSeed] = useState(0);

  const { jobState, startJob } = useJobManager();

  // Backend Health Check
  useEffect(() => {
    const check = async () => {
      const isAlive = await ArcheonClient.healthCheck();
      setStatus(isAlive ? "connected" : "disconnected");
    };
    check();
    const interval = setInterval(check, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerate = () => {
    if (mode === "text_to_3d" && !prompt) return;
    if (mode === "image_to_3d" && !imagePath) return;

    startJob(
      mode,
      {
        text_prompt: prompt,
        negative_prompt: negPrompt,
        seed: seed,
        imagePath: imagePath
      },
      {
        steps: steps,
        guidance_scale: guidance
      }
    );
  };

  const getStatusColor = (s: string) => {
    if (s === "completed") return "text-green-500";
    if (s === "failed") return "text-red-500";
    if (s === "generating") return "text-blue-500";
    if (s === "queued") return "text-yellow-500";
    return "text-muted-foreground";
  }

  const sidebarContent = (
    <div className="space-y-6">

      {/* Status Bar */}
      <div className="space-y-2">
        <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">System Status</label>
        <div className={`p-2 rounded border bg-card flex justify-between items-center text-xs ${status === "connected" ? "border-green-900/30 text-green-500" : "border-red-900/30 text-red-500"}`}>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${status === "connected" ? "bg-green-500" : "bg-red-500 animate-pulse"}`} />
            <span className="font-semibold">{status === "connected" ? "ONLINE" : "OFFLINE"}</span>
          </div>
          <span className="opacity-50">Localhost:8081</span>
        </div>
      </div>

      <div className="h-px bg-border" />

      {/* Mode Tabs */}
      <Tabs defaultValue="text" onValueChange={(v) => setMode(v === "text" ? "text_to_3d" : "image_to_3d")}>
        <TabsList>
          <TabsTrigger value="text">Text to 3D</TabsTrigger>
          <TabsTrigger value="image">Image to 3D</TabsTrigger>
        </TabsList>

        {/* Text Mode */}
        <TabsContent value="text" className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label>Text Prompt</Label>
            <textarea
              className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Ex: A futuristic cybernetic helmet with neon lights..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>
        </TabsContent>

        {/* Image Mode */}
        <TabsContent value="image" className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label>Source Image</Label>
            <ImageUpload
              onImageSelected={(path) => setImagePath(path)}
              selectedImage={imagePath}
            />
          </div>
        </TabsContent>
      </Tabs>

      {/* Common Parameters */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Negative Prompt</Label>
          <Input
            value={negPrompt}
            onChange={(e) => setNegPrompt(e.target.value)}
            placeholder="bad quality, blurry..."
          />
        </div>

        <div className="space-y-4 pt-4 border-t border-border">
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Inference Steps</Label>
              <span className="text-xs text-muted-foreground">{steps}</span>
            </div>
            <Slider
              min={15} max={50} step={1}
              value={steps}
              onChange={(e) => setSteps(Number(e.target.value))}
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Guidance Scale</Label>
              <span className="text-xs text-muted-foreground">{guidance}</span>
            </div>
            <Slider
              min={1.0} max={15.0} step={0.5}
              value={guidance}
              onChange={(e) => setGuidance(Number(e.target.value))}
            />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Seed</Label>
              <span className="text-xs text-muted-foreground">{seed}</span>
            </div>
            <Input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
            />
          </div>
        </div>
      </div>

      <div className="pt-6">
        <button
          onClick={handleGenerate}
          disabled={status !== "connected" || jobState.status === "generating" || jobState.status === "queued"}
          className="w-full inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-bold ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
        >
          {jobState.status === "generating" || jobState.status === "queued" ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generando...
            </span>
          ) : "Generate 3D Model"}
        </button>
      </div>

      {/* Job Status Card */}
      {jobState.status !== "idle" && (
        <div className={`mt-4 p-3 rounded-md border text-sm ${getStatusColor(jobState.status)} bg-card`}>
          <div className="flex justify-between items-center mb-1">
            <span className="font-bold uppercase text-[10px]">Job Status</span>
            <span className="text-[10px]">{jobState.status.toUpperCase()}</span>
          </div>
          {jobState.error && (
            <div className="text-xs mt-1 text-red-500 break-words font-mono bg-red-950/20 p-2 rounded">
              {jobState.error}
            </div>
          )}
        </div>
      )}

    </div>
  );

  const meshUrl = jobState.resultUrl ? convertFileSrc(jobState.resultUrl) : undefined;

  return (
    <AppLayout sidebar={sidebarContent}>
      <SidecarManager />
      <Viewer3D modelUrl={meshUrl} />
    </AppLayout>
  );
}

export default App;
