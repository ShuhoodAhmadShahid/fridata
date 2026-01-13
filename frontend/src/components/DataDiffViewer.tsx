import React from 'react';
import { ColumnProfile } from '@/lib/api';

interface DataDiffViewerProps {
    originalData: Record<string, any>[]; // Preview of original
    cleanedData?: Record<string, any>[];  // Preview of cleaned (optional)
    columns: ColumnProfile[];
}

export const DataDiffViewer: React.FC<DataDiffViewerProps> = ({ originalData, cleanedData, columns }) => {

    // We only show side-by-side if we have cleanedData
    // Otherwise just show Original Data Table

    const showDiff = !!cleanedData;

    return (
        <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 rounded-lg border border-slate-800">
            <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 flex justify-between items-center">
                <h3 className="text-sm font-semibold text-slate-300">
                    {showDiff ? "Data Diff (Preview)" : "Data Preview"}
                </h3>
                <div className="text-xs text-slate-500 font-mono">
                    {columns.length} columns
                </div>
            </div>

            <div className="flex-1 overflow-auto">
                <div className="flex min-w-full">
                    {/* Left Pane: Original or Main View */}
                    <div className={`flex-1 ${showDiff ? 'border-r border-slate-800' : ''}`}>
                        <table className="w-full text-left text-xs text-slate-400 font-mono whitespace-nowrap">
                            <thead className="bg-slate-900 text-slate-500 sticky top-0 z-10">
                                <tr>
                                    <th className="px-4 py-2 border-b border-slate-800 w-12 text-right">#</th>
                                    {columns.map(col => (
                                        <th key={col.name} className="px-4 py-2 border-b border-slate-800">
                                            {col.name} <span className="opacity-50 text-[10px]">({col.dtype})</span>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/50">
                                {originalData.map((row, i) => (
                                    <tr key={i} className="hover:bg-slate-900/50 transition-colors">
                                        <td className="px-4 py-2 border-r border-slate-800/50 text-right opacity-50 bg-slate-900/30">
                                            {i + 1}
                                        </td>
                                        {columns.map(col => (
                                            <td
                                                key={`${i}-${col.name}`}
                                                className={`px-4 py-2 ${showDiff && cleanedData && cleanedData[i] === undefined ? 'line-through text-red-500/50' : ''}`}
                                            >
                                                {String(row[col.name] ?? '')}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Right Pane: Cleaned View (Diff) */}
                    {showDiff && cleanedData && (
                        <div className="flex-1 bg-slate-950/50">
                            <table className="w-full text-left text-xs text-slate-400 font-mono whitespace-nowrap">
                                <thead className="bg-slate-900 text-slate-500 sticky top-0 z-10">
                                    <tr>
                                        {columns.map(col => (
                                            <th key={col.name} className="px-4 py-2 border-b border-slate-800">
                                                {col.name}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800/50">
                                    {cleanedData.map((row, i) => (
                                        <tr key={i} className="hover:bg-slate-900/50 transition-colors">
                                            {columns.map(col => {
                                                const originalVal = originalData[i] ? originalData[i][col.name] : undefined;
                                                const newVal = row[col.name];
                                                const isChanged = originalData[i] && String(originalVal) !== String(newVal);

                                                return (
                                                    <td
                                                        key={`${i}-${col.name}`}
                                                        className={`px-4 py-2 transition-colors duration-500 ${isChanged ? 'bg-emerald-500/10 text-emerald-400' : ''}`}
                                                    >
                                                        {String(newVal ?? '')}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
