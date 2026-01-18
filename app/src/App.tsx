import { useState, useEffect } from "react";
import "./App.css";
import { ArcheonClient } from "./lib/api";
import { AppLayout } from "./components/layout/AppLayout";
import { Viewer3D } from "./components/viewer/Viewer3D";

function App() {
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [inputText, setInputText] = useState("");

  useEffect(() => {
    const check = async () => {
      const isAlive = await ArcheonClient.healthCheck();
      setStatus(isAlive ? "connected" : "disconnected");
    };
    check();
    const interval = setInterval(check, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerate = async () => {
    console.log("Generate:", inputText);
  };

  const sidebarContent = (
    <div className="space-y-6">
      <div className="space-y-2">
        <label className="text-sm font-medium">Backend Status</label>
        <div className={`text-xs flex items-center gap-2 p-2 rounded border bg-background ${status === "connected" ? "border-green-800 text-green-500" : "border-red-800 text-red-500"}`}>
          <div className={`w-2 h-2 rounded-full ${status === "connected" ? "bg-green-500" : "bg-red-500"}`} />
          {status.toUpperCase()}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Text Prompt</label>
        <textarea
          className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          placeholder="A futuristic cybernetic helmet..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        />
      </div>

      <button onClick={handleGenerate} className="w-full inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2">
        Generate 3D
      </button>
    </div>
  );

  return (
    <AppLayout sidebar={sidebarContent}>
      <Viewer3D />
    </AppLayout>
  );
}

export default App;
