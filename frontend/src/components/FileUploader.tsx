import React, { useCallback, useState } from 'react';
import { Upload } from 'lucide-react';
import { cn } from '@/lib/utils'; // Assuming separate utils or inline it? Prompt didn't specify utils file but referred to cn.


interface FileUploaderProps {
    onUpload: (file: File) => void;
    isUploading: boolean;
    progress: number;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onUpload, isUploading, progress }) => {
    const [isDragging, setIsDragging] = useState(false);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setIsDragging(true);
        } else if (e.type === 'dragleave') {
            setIsDragging(false);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            onUpload(e.dataTransfer.files[0]);
        }
    }, [onUpload]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            onUpload(e.target.files[0]);
        }
    };

    return (
        <div
            className={cn(
                "relative flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg transition-colors duration-200 ease-in-out cursor-pointer",
                isDragging ? "border-indigo-500 bg-slate-800/50" : "border-slate-700 bg-slate-900",
                isUploading ? "pointer-events-none opacity-50" : "hover:bg-slate-800"
            )}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
        >
            <input
                type="file"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                onChange={handleChange}
                accept=".csv, .xlsx, .xls"
                disabled={isUploading}
            />

            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <Upload className={cn("w-10 h-10 mb-3", isDragging ? "text-indigo-400" : "text-slate-400")} />
                <p className="mb-2 text-sm text-slate-400">
                    <span className="font-semibold">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-slate-500">CSV or Excel (MAX. 50MB)</p>
            </div>

            {isUploading && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 rounded-lg">
                    <div className="w-64">
                        <div className="flex justify-between mb-1">
                            <span className="text-sm font-medium text-emerald-500">Uploading...</span>
                            <span className="text-sm font-medium text-emerald-500">{progress}%</span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2.5">
                            <div
                                className="bg-emerald-500 h-2.5 rounded-full transition-all duration-300"
                                style={{ width: `${progress}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
