import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Types based on Pydantic models
export interface ColumnProfile {
    name: string;
    dtype: string;
    null_count: number;
    unique_count: number;
    sample_values: any[];
}

export interface DatasetProfile {
    job_id: string;
    filename: string;
    total_rows: number;
    columns: ColumnProfile[];
    preview: Record<string, any>[];
}

export interface TransformStep {
    operation: string;
    parameters: Record<string, any>;
    target_column?: string | null;
    explanation?: string;
}

export interface PlanResponse {
    job_id: string;
    steps: TransformStep[];
    estimated_impact: string;
}

export interface ExecutionResult {
    job_id: string;
    status: 'pending' | 'analyzing' | 'ready' | 'processing' | 'completed' | 'failed';
    download_url?: string | null;
    metrics: Record<string, any>;
    error?: string | null;
    preview?: Record<string, any>[];
}

// API Methods
export const uploadFile = async (file: File, onProgress: (progress: number) => void): Promise<DatasetProfile> => {
    const formData = new FormData();
    formData.append('file', file);

    // Manual 50MB check client-side
    if (file.size > 50 * 1024 * 1024) {
        // Warning logic or hard block if strictly enforcing free tier
        console.warn("Large file detected.");
    }

    const { data } = await api.post<DatasetProfile>('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
            onProgress(percentCompleted);
        }
    });
    return data;
};

export const generatePlan = async (jobId: string, prompt: string): Promise<PlanResponse> => {
    const { data } = await api.post<PlanResponse>('/transform', { job_id: jobId, prompt });
    return data;
};

export const executePlan = async (jobId: string): Promise<ExecutionResult> => {
    const { data } = await api.post<ExecutionResult>('/execute', { job_id: jobId, approved: true });
    return data;
};
