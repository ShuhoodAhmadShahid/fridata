import { useState, useEffect } from 'react';
import { useDataTransform } from '@/hooks/useDataTransform';
import { FileUploader } from '@/components/FileUploader';
import { ChatCommand } from '@/components/ChatCommand';
import { DataDiffViewer } from '@/components/DataDiffViewer';
import { Play, AlertTriangle, CheckCircle, FileText } from 'lucide-react';

function App() {
    const {
        jobId,
        datasetProfile,
        currentData,
        proposedSteps,
        isProcessing,
        error,
        uploadProgress,
        executionResult,
        handleUpload,
        handleTransformRequest,
        handleExecute,
        reset
    } = useDataTransform();

    const [history, setHistory] = useState<{ role: 'user' | 'ai', content: string }[]>([
        { role: 'ai', content: "Ready. Upload a dataset to begin." }
    ]);

    // Effect to update Chat when a Plan is proposed
    useEffect(() => {
        if (proposedSteps.length > 0) {
            const stepsList = proposedSteps.map((s, i) => `${i + 1}. [ ] ${s.operation}: ${JSON.stringify(s.parameters)}`).join('\n');
            setHistory(prev => [...prev, {
                role: 'ai',
                content: `I have generated a plan:\n${stepsList}\n\nPlease confirm to execute.`
            }]);
        }
    }, [proposedSteps]);

    // Effect to update Chat when Execution is done
    useEffect(() => {
        if (executionResult) {
            if (executionResult.status === 'completed') {
                setHistory(prev => [...prev, {
                    role: 'ai',
                    content: `Transformation Complete!\nProcessed ${executionResult.metrics.input_rows} rows in ${executionResult.metrics.execution_time_sec}s.\n\nUsage: ${executionResult.metrics.memory_usage_mb} MB.`
                }]);
            } else if (executionResult.status === 'failed') {
                setHistory(prev => [...prev, {
                    role: 'ai',
                    content: `Execution Failed: ${executionResult.error}`
                }]);
            }
        }
    }, [executionResult]);

    const onChatSubmit = async (text: string) => {
        setHistory(prev => [...prev, { role: 'user', content: text }]);
        await handleTransformRequest(text);
    };

    const onConfirmPlan = async () => {
        setHistory(prev => [...prev, { role: 'user', content: "Confirmed. Execute plan." }]);
        await handleExecute();
        // Clear proposed steps from state logic would be handled by hook or we just hide the button
        // For MVP, we keep the state but maybe disable button
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-indigo-500/30">

            {/* Navbar / Header */}
            <header className="h-14 border-b border-slate-800 flex items-center px-6 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                        <FileText className="w-5 h-5 text-white" />
                    </div>
                    <h1 className="font-bold text-lg tracking-tight">FRIDATA <span className="text-slate-500 text-xs font-mono ml-2">v1.0</span></h1>
                </div>
                <div className="ml-auto flex items-center space-x-4">
                    {jobId && (
                        <div className="flex items-center space-x-2 text-xs font-mono text-slate-500 bg-slate-900 px-3 py-1 rounded-full border border-slate-800">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                            <span>{datasetProfile?.filename}</span>
                        </div>
                    )}
                    {jobId && (
                        <button onClick={reset} className="text-xs text-slate-400 hover:text-white transition-colors">
                            Reset
                        </button>
                    )}
                </div>
            </header>

            {/* Main Content */}
            <main className="h-[calc(100vh-3.5rem)] p-4 flex gap-4 overflow-hidden">

                {/* Left Sidebar: Controls (30%) */}
                <div className="w-[400px] flex flex-col space-y-4 shrink-0">

                    {/* Upload Area */}
                    {!jobId ? (
                        <div className="mt-10">
                            <FileUploader
                                onUpload={handleUpload}
                                isUploading={isProcessing && !datasetProfile}
                                progress={uploadProgress}
                            />
                        </div>
                    ) : (
                        <>
                            {/* Chat Interface */}
                            <div className="flex-1 min-h-0">
                                <ChatCommand
                                    history={history}
                                    onSubmit={onChatSubmit}
                                    isProcessing={isProcessing}
                                />
                            </div>
                        </>
                    )}

                    {/* Global Error Display */}
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 flex items-start space-x-3 text-red-200 text-sm">
                            <AlertTriangle className="w-5 h-5 shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Plan Confirmation Action */}
                    {proposedSteps.length > 0 && !executionResult && !isProcessing && (
                        <div className="bg-indigo-900/20 border border-indigo-500/30 p-4 rounded-lg animate-in fade-in slide-in-from-bottom-4">
                            <h4 className="text-sm font-semibold text-indigo-300 mb-2">Confirm Execution?</h4>
                            <p className="text-xs text-slate-400 mb-4">
                                This will apply {proposedSteps.length} transformation steps to your dataset.
                            </p>
                            <button
                                onClick={onConfirmPlan}
                                className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-md font-medium transition-all"
                            >
                                <Play className="w-4 h-4" />
                                <span>Execute Plan</span>
                            </button>
                        </div>
                    )}

                    {/* Download Result */}
                    {executionResult?.download_url && (
                        <div className="bg-emerald-900/20 border border-emerald-500/30 p-4 rounded-lg animate-in fade-in">
                            <h4 className="text-sm font-semibold text-emerald-300 mb-2">Processing Complete</h4>
                            <a
                                href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/download/${jobId}`}
                                download
                                className="flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white w-full py-2 rounded-md font-medium transition-all"
                            >
                                <CheckCircle className="w-4 h-4" />
                                <span>Download Cleaned CSV</span>
                            </a>
                        </div>
                    )}

                </div>

                {/* Right Pane: Data View (70%) */}
                <div className="flex-1 flex flex-col min-w-0">
                    {datasetProfile ? (
                        <DataDiffViewer
                            originalData={currentData}
                            cleanedData={executionResult?.preview ?? undefined}
                            columns={datasetProfile.columns}
                        />
                    ) : (
                        // Empty State
                        <div className="flex-1 flex items-center justify-center border border-dashed border-slate-800 rounded-lg bg-slate-900/30">
                            <div className="text-center text-slate-600">
                                <FileText className="w-16 h-16 mx-auto mb-4 opacity-20" />
                                <p>Upload a file to view data</p>
                            </div>
                        </div>
                    )}
                </div>

            </main>
        </div>
    );
}

export default App;
