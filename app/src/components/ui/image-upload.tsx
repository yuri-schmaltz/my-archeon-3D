import { useState } from "react";
import { cn } from "../../lib/utils";
import { convertFileSrc } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";

interface ImageUploadProps {
    onImageSelected: (path: string) => void;
    selectedImage?: string;
}

export function ImageUpload({ onImageSelected, selectedImage }: ImageUploadProps) {
    // Drag state removed for now as we use click-to-open logic
    const [preview, setPreview] = useState<string | null>(null);

    const handleFileSelect = async () => {
        try {
            const file = await open({
                multiple: false,
                directory: false,
                filters: [{
                    name: 'Images',
                    extensions: ['png', 'jpg', 'jpeg', 'webp']
                }]
            });

            if (file) {
                // file is string path or Asset object? In v2 plugin-dialog it returns path string or null
                // Check types if we were strict, but let's assume string
                const path = file as string;
                onImageSelected(path);
                setPreview(convertFileSrc(path));
            }
        } catch (e) {
            console.error("Dialog error", e);
        }
    };

    // For Drag and Drop we need tauri's file-drop event listener usually, 
    // or standard HTML5 events if tauri configured to allow it.
    // Standard HTML5 DnD gives File object, but we need the path. 
    // Web File API in Tauri window might not give full path.
    // For simplicity MVP: Use the Click-to-Open dialog effectively.

    // NOTE: React Dropzone gives File objects. 
    // In Tauri (Chromium), File.path is often exposed directly or we can rely on `open`.

    return (
        <div
            onClick={handleFileSelect}
            className={cn(
                "border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer transition-colors h-48",
                "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50",
                selectedImage ? "p-0 overflow-hidden border-solid" : ""
            )}
        >
            {selectedImage || preview ? (
                <img
                    src={preview || convertFileSrc(selectedImage!)}
                    alt="Selected"
                    className="w-full h-full object-contain"
                />
            ) : (
                <div className="text-center space-y-2 pointer-events-none">
                    <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center mx-auto">
                        <svg className="w-5 h-5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                    </div>
                    <div className="text-xs text-muted-foreground">
                        <span className="font-semibold text-primary">Click to upload</span> an image
                    </div>
                    <p className="text-[10px] text-muted-foreground/70">
                        PNG, JPG, WEBP
                    </p>
                </div>
            )}
        </div>
    );
}
