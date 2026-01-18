import { ReactNode } from "react";

interface AppLayoutProps {
    children: ReactNode;
    sidebar: ReactNode;
}

export function AppLayout({ children, sidebar }: AppLayoutProps) {
    return (
        <div className="flex h-screen w-screen overflow-hidden bg-background">
            {/* Sidebar */}
            <aside className="w-80 border-r border-border bg-card flex flex-col">
                <div className="p-4 border-b border-border">
                    <h1 className="text-xl font-bold tracking-tight">Archeon 3D</h1>
                    <p className="text-xs text-muted-foreground">AEGIS ONE Engine</p>
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {sidebar}
                </div>
                <div className="p-4 border-t border-border text-xs text-muted-foreground text-center">
                    Tauri Beta v0.1.0
                </div>
            </aside>

            {/* Main Content (3D Viewport) */}
            <main className="flex-1 relative bg-neutral-900 overflow-hidden">
                {children}
            </main>
        </div>
    );
}
