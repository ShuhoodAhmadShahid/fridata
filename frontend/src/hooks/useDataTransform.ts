import { useState } from 'react';
import {
    DatasetProfile, TransformStep, ExecutionResult,
    uploadFile, generatePlan, executePlan
} from '@/lib/api';

export const useDataTransform = () => {
    const [jobId, setJobId] = useState<string | null>(null);
    const [datasetProfile, setDatasetProfile] = useState<DatasetProfile | null>(null);
    const [proposedSteps, setProposedSteps] = useState<TransformStep[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);

    // For Diff Viewer (Simplified: currentData is the preview)
    const [currentData, setCurrentData] = useState<Record<string, any>[]>([]);

    const handleUpload = async (file: File) => {
        setIsProcessing(true);
        setError(null);
        setUploadProgress(0);
        try {
            const profile = await uploadFile(file, (p) => setUploadProgress(p));
            setJobId(profile.job_id);
            setDatasetProfile(profile);
            setCurrentData(profile.preview);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Upload failed");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleTransformRequest = async (prompt: string) => {
        if (!jobId) return;
        setIsProcessing(true);
        setError(null);
        try {
            const plan = await generatePlan(jobId, prompt);
            setProposedSteps(plan.steps); // Triggers UI to show confirmation
        } catch (err: any) {
            setError(err.response?.data?.detail || "Planning failed");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleExecute = async () => {
        if (!jobId) return;
        setIsProcessing(true);
        setError(null);
        try {
            const result = await executePlan(jobId);
            setExecutionResult(result);
            if (result.status === 'failed') {
                setError(result.error || "Execution failed");
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || "Execution failed");
        } finally {
            setIsProcessing(false);
        }
    };

    const reset = () => {
        setJobId(null);
        setDatasetProfile(null);
        setProposedSteps([]);
        setExecutionResult(null);
        setCurrentData([]);
        setError(null);
        setUploadProgress(0);
    };

    return {
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
    };
};
