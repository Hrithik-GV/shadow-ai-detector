import React, { useState, useRef } from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Card } from '../components/common/Card';
import { Table, type Column } from '../components/common/Table';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { useSubmitTrafficFile, useTrafficAnalysis } from '../hooks/useTraffic';
import { Upload, FileUp, RefreshCw, CheckCircle2 } from 'lucide-react';
import type { TrafficRecord } from '../types';

export const TrafficPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeAnalysisId, setActiveAnalysisId] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    mutate: submitFile,
    isPending: isUploading,
    isError: isUploadError,
    error: uploadError,
    data: uploadResult,
    reset: resetUpload,
  } = useSubmitTrafficFile();

  const {
    data: analysisData,
    isLoading: isLoadingAnalysis,
    isError: isAnalysisError,
    error: analysisError,
    refetch: refetchAnalysis,
  } = useTrafficAnalysis(activeAnalysisId);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      resetUpload();
    }
  };

  const handleUploadSubmit = () => {
    if (!selectedFile) return;
    submitFile(selectedFile, {
      onSuccess: (data) => {
        if (data.analysisId) {
          setActiveAnalysisId(data.analysisId);
        }
      },
    });
  };

  const columns: Column<TrafficRecord>[] = [
    {
      key: 'timestamp',
      header: 'TIMESTAMP',
      width: '180px',
      render: (item) => <span className="text-[#9A9A91]">{item.timestamp}</span>,
    },
    {
      key: 'sourceIp',
      header: 'SOURCE IP',
      width: '140px',
      render: (item) => <span className="text-[#F4F4F0] font-bold">{item.sourceIp}</span>,
    },
    {
      key: 'destinationHost',
      header: 'DESTINATION HOST',
      render: (item) => <span className="text-[#FFCC00]">{item.destinationHost}</span>,
    },
    {
      key: 'protocol',
      header: 'PROTOCOL',
      width: '100px',
      render: (item) => <Badge variant="muted">{item.protocol}</Badge>,
    },
    {
      key: 'provider',
      header: 'PROVIDER',
      render: (item) => <span className="text-[#F4F4F0]">{item.provider || '-'}</span>,
    },
    {
      key: 'riskLevel',
      header: 'RISK LEVEL',
      width: '120px',
      render: (item) => (
        <Badge
          variant={
            item.riskLevel === 'high' || item.riskLevel === 'critical'
              ? 'danger'
              : item.riskLevel === 'medium'
              ? 'warning'
              : 'default'
          }
        >
          {item.riskLevel}
        </Badge>
      ),
    },
  ];

  return (
    <PageContainer
      title="Traffic Analysis"
      description="Inspect network telemetry, outbound AI payload streams, and analyze packet capture files."
      badge={<Badge variant="accent">MULTIPART INGESTION</Badge>}
      actions={
        activeAnalysisId ? (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => refetchAnalysis()}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            REFRESH ANALYSIS
          </Button>
        ) : undefined
      }
    >
      {/* Upload File Panel: POST /api/traffic/analyze */}
      <Card
        variant="charcoal"
        title="Submit Traffic File For Analysis"
        subtitle="Upload network capture (PCAP, PCAPNG) or JSON packet stream logs for AI detection. Sent via multipart/form-data."
        headerIcon={<FileUp className="w-5 h-5 text-[#FFCC00]" />}
      >
        <div className="space-y-4 font-mono text-xs">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pcap,.pcapng,.json,.csv,.log"
            className="hidden"
          />

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <Button
              variant="secondary"
              size="sm"
              icon={<Upload className="w-3.5 h-3.5" />}
              onClick={() => fileInputRef.current?.click()}
            >
              {selectedFile ? 'CHANGE FILE' : 'SELECT TRAFFIC FILE'}
            </Button>

            {selectedFile && (
              <span className="text-[#F4F4F0] bg-[#0D0D0D] px-3 py-1.5 border border-[#333330] flex-1 truncate">
                {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </span>
            )}

            {selectedFile && (
              <Button
                variant="primary"
                size="sm"
                onClick={handleUploadSubmit}
                disabled={isUploading}
                icon={<Upload className={`w-3.5 h-3.5 ${isUploading ? 'animate-bounce' : ''}`} />}
              >
                {isUploading ? 'SUBMITTING...' : 'START ANALYSIS'}
              </Button>
            )}
          </div>

          {/* Upload Status / Errors */}
          {isUploadError && (
            <QueryErrorState
              title="File Submission Failed"
              error={uploadError}
              onRetry={handleUploadSubmit}
              isRetrying={isUploading}
            />
          )}

          {uploadResult && (
            <div className="p-3 bg-[#0D0D0D] border border-[#00E575]/40 text-[#00E575] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#00E575]" />
                <span>
                  {uploadResult.message || 'File submitted successfully.'} Analysis ID:{' '}
                  <strong>{uploadResult.analysisId}</strong>
                </span>
              </div>
              <Badge variant="success" size="sm">
                STATUS: {uploadResult.status.toUpperCase()}
              </Badge>
            </div>
          )}
        </div>
      </Card>

      {/* Analysis Results / Query */}
      {activeAnalysisId && isLoadingAnalysis && (
        <LoadingState message={`RETRIEVING ANALYSIS JOB [${activeAnalysisId}]...`} />
      )}

      {activeAnalysisId && isAnalysisError && (
        <QueryErrorState
          title={`Analysis Job Error [${activeAnalysisId}]`}
          error={analysisError}
          onRetry={() => refetchAnalysis()}
        />
      )}

      {/* Table displaying real records or honest empty state */}
      <Table
        columns={columns}
        data={analysisData?.records || []}
        keyExtractor={(item) => item.id}
        emptyTitle="No Traffic Telemetry Recorded"
        emptyDescription="No network traffic records found. Upload a traffic capture file above or connect an active network sensor stream."
      />
    </PageContainer>
  );
};
