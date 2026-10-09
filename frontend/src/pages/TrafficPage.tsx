import React, { useState, useRef, useMemo } from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { useSubmitTrafficFile, useTrafficAnalysis } from '../hooks/useTraffic';
import {
  Upload,
  FileText,
  RefreshCw,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Loader2,
  Radio,
  Info,
} from 'lucide-react';

const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB
const ALLOWED_EXTENSIONS = ['.csv', '.json', '.jsonl', '.ndjson', '.pcap', '.pcapng', '.cap'];

export const TrafficPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [activeAnalysisId, setActiveAnalysisId] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Filter & Pagination States
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 10;

  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    mutate: submitFile,
    isPending: isUploading,
    isError: isUploadError,
    error: uploadError,
    reset: resetUploadMutation,
  } = useSubmitTrafficFile();

  const {
    data: analysisResult,
    isLoading: isLoadingAnalysis,
    isError: isAnalysisError,
    error: analysisError,
    refetch: refetchAnalysis,
    isFetching: isFetchingAnalysis,
  } = useTrafficAnalysis(activeAnalysisId);

  // Validate file format and size
  const validateFile = (file: File): string | null => {
    const fileName = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_EXTENSIONS.some((ext) => fileName.endsWith(ext));

    if (!hasValidExtension) {
      return 'Unsupported file format. Supported capture and log formats: .pcap, .pcapng, .cap, .csv, .json, .jsonl, .ndjson.';
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds maximum allowed limit of 50 MB.`;
    }

    return null;
  };

  const handleFileSelection = (file: File) => {
    const errorMsg = validateFile(file);
    if (errorMsg) {
      setValidationError(errorMsg);
      setSelectedFile(null);
      return;
    }
    setValidationError(null);
    setSelectedFile(file);
    setUploadProgress(0);
    resetUploadMutation();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleUploadSubmit = () => {
    if (!selectedFile) return;

    setUploadProgress(0);
    submitFile(
      {
        file: selectedFile,
        onProgress: (percent) => setUploadProgress(percent),
      },
      {
        onSuccess: (response) => {
          const id = response.id || response.analysisId;
          if (id) {
            setActiveAnalysisId(id);
            setCurrentPage(1);
          }
        },
      }
    );
  };

  const handleReset = () => {
    setSelectedFile(null);
    setValidationError(null);
    setActiveAnalysisId('');
    setUploadProgress(0);
    setSearchTerm('');
    setRiskFilter('all');
    setCurrentPage(1);
    resetUploadMutation();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Safe client-side filtering on returned records
  const filteredRecords = useMemo(() => {
    const records = analysisResult?.records || [];
    return records.filter((rec) => {
      const src = rec.sourceIp || rec.source_ip || '';
      const dest =
        rec.destinationHost ||
        rec.destinationDomain ||
        rec.destination_domain ||
        rec.destinationIp ||
        rec.destination_ip ||
        rec.sni_hostname ||
        '';
      const proto = rec.protocol || '';
      const prov = rec.provider || '';

      const matchesSearch =
        searchTerm === '' ||
        src.toLowerCase().includes(searchTerm.toLowerCase()) ||
        dest.toLowerCase().includes(searchTerm.toLowerCase()) ||
        proto.toLowerCase().includes(searchTerm.toLowerCase()) ||
        prov.toLowerCase().includes(searchTerm.toLowerCase());

      const risk = (rec.riskLevel || rec.risk_level || rec.classification || '').toLowerCase();
      const matchesRisk =
        riskFilter === 'all' ||
        risk === riskFilter.toLowerCase();

      return matchesSearch && matchesRisk;
    });
  }, [analysisResult?.records, searchTerm, riskFilter]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredRecords.length / pageSize));
  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRecords.slice(start, start + pageSize);
  }, [filteredRecords, currentPage, pageSize]);

  const isAnalysisProcessing =
    analysisResult?.status === 'pending' || analysisResult?.status === 'processing';
  const isAnalysisFailed = analysisResult?.status === 'failed';
  const isAnalysisCompleted = analysisResult?.status === 'completed';

  return (
    <PageContainer
      title="Traffic Analysis"
      description="Inspect network telemetry, submit traffic captures (CSV/JSON) via multipart/form-data, and monitor deep detection findings."
      badge={
        activeAnalysisId ? (
          <Badge variant="accent">JOB: {activeAnalysisId}</Badge>
        ) : (
          <Badge variant="default">READY FOR INGESTION</Badge>
        )
      }
      actions={
        <div className="flex items-center gap-2">
          {activeAnalysisId && (
            <Button
              variant="outline"
              size="sm"
              icon={<RotateCcw className="w-3.5 h-3.5" />}
              onClick={handleReset}
            >
              NEW ANALYSIS
            </Button>
          )}
          {activeAnalysisId && (
            <Button
              variant="secondary"
              size="sm"
              icon={<RefreshCw className={`w-3.5 h-3.5 ${isFetchingAnalysis ? 'animate-spin' : ''}`} />}
              onClick={() => refetchAnalysis()}
              disabled={isFetchingAnalysis}
            >
              REFRESH
            </Button>
          )}
        </div>
      }
    >
      {/* 1. File Upload Dropzone (visible if no completed analysis or user wants to re-upload) */}
      {!activeAnalysisId && (
        <Card
          variant="charcoal"
          title="Traffic Capture & Log File Ingestion"
          subtitle="Submit network captures (.pcap, .pcapng, .cap) or structured logs (.csv, .json) up to 50 MB for AI detection and risk assessment."
          headerIcon={<Upload className="w-5 h-5 text-[#FFCC00]" />}
        >
          <div className="space-y-4 font-mono text-xs">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleInputChange}
              accept=".csv,.json,.jsonl,.ndjson,.pcap,.pcapng,.cap"
              className="hidden"
            />

            {/* Drag and Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-120 select-none ${
                isDragging
                  ? 'border-[#FFCC00] bg-[#181818] shadow-[4px_4px_0_#735C00]'
                  : 'border-[#333330] hover:border-[#FFCC00] bg-[#121212] hover:bg-[#181818]'
              }`}
            >
              <div className="flex flex-col items-center justify-center space-y-3">
                <div className="w-12 h-12 bg-[#181818] border-2 border-[#333330] shadow-[2px_2px_0_#000000] flex items-center justify-center text-[#FFCC00]">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <p className="font-bold text-[#F4F4F0] uppercase tracking-wide text-sm">
                    {selectedFile ? selectedFile.name : 'DRAG & DROP TRAFFIC OR CAPTURE FILE HERE'}
                  </p>
                  <p className="text-[#9A9A91] text-[11px] mt-1">
                    {selectedFile
                      ? `Size: ${(selectedFile.size / 1024).toFixed(1)} KB — Click or drop to change`
                      : 'or click to browse local files (.PCAP, .PCAPNG, .CSV, .JSON)'}
                  </p>
                </div>
                <div className="flex items-center gap-2 pt-1 flex-wrap justify-center">
                  <Badge variant="accent" size="sm">PCAP</Badge>
                  <Badge variant="accent" size="sm">PCAPNG</Badge>
                  <Badge variant="muted" size="sm">CSV</Badge>
                  <Badge variant="muted" size="sm">JSON</Badge>
                  <Badge variant="muted" size="sm">MAX 50MB</Badge>
                </div>
              </div>
            </div>

            {/* Capture Capabilities & Scope Note */}
            <div className="p-3 bg-[#171716] border border-[#2B2B28] text-[11px] text-[#9A9A91] space-y-1.5 leading-relaxed">
              <div className="flex items-center gap-2 text-[#F4F4F0] font-bold uppercase tracking-wider text-[10px]">
                <Info className="w-3.5 h-3.5 text-[#FFCC00]" />
                <span>Capture Analysis Scope & Wire Byte Semantics</span>
              </div>
              <p>
                <strong className="text-[#E0E0DC]">Supported Metadata:</strong> Timestamps, IP 5-tuples, transport protocols (TCP/UDP), DNS queries and A/AAAA resolutions, and TLS Server Name Indication (SNI) hostnames via RFC 6066.
              </p>
              <p>
                <strong className="text-[#E0E0DC]">Security Boundary:</strong> Operates strictly on uploaded captures in userspace without requiring live sniffing privileges or TLS payload decryption. Plain IP flows without SNI or DNS evidence are never guessed.
              </p>
              <p>
                <strong className="text-[#E0E0DC]">Byte Definitions:</strong> Measured bytes represent Layer 3 IP wire length. Network bytes do not reveal prompt contents or artificial token billing metrics.
              </p>
            </div>

            {/* Client Validation Error State */}
            {validationError && (
              <div className="p-3 bg-[#2A1616] border border-[#8C2323] text-[#FF6B6B] flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-[#FF6B6B]" />
                <span>{validationError}</span>
              </div>
            )}

            {/* Upload Action Button & Progress */}
            {selectedFile && !validationError && (
              <div className="space-y-3 pt-2">
                {isUploading && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] text-[#9A9A91]">
                      <span>UPLOADING TO POST /api/traffic/analyze</span>
                      <span className="text-[#FFCC00] font-bold">{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-[#181818] border border-[#333330] h-2.5">
                      <div
                        className="bg-[#FFCC00] h-full transition-all duration-150"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-end gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleReset}
                    disabled={isUploading}
                  >
                    CANCEL
                  </Button>
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleUploadSubmit}
                    disabled={isUploading}
                    icon={
                      isUploading ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Upload className="w-3.5 h-3.5" />
                      )
                    }
                  >
                    {isUploading ? 'SUBMITTING FILE...' : 'SUBMIT FOR ANALYSIS'}
                  </Button>
                </div>
              </div>
            )}

            {/* Upload API Error */}
            {isUploadError && (
              <QueryErrorState
                title="File Upload Failed"
                error={uploadError}
                onRetry={handleUploadSubmit}
                isRetrying={isUploading}
              />
            )}
          </div>
        </Card>
      )}

      {/* 2. Loading initial analysis */}
      {activeAnalysisId && isLoadingAnalysis && (
        <LoadingState message={`RETRIEVING ANALYSIS JOB [${activeAnalysisId}]...`} />
      )}

      {/* 3. Processing / In-Progress Analysis State */}
      {activeAnalysisId && !isLoadingAnalysis && isAnalysisProcessing && (
        <Card variant="charcoal" title="Analysis Job In Progress">
          <div className="p-6 text-center space-y-4">
            <div className="w-12 h-12 mx-auto bg-[#181818] border-2 border-[#FFCC00] shadow-[3px_3px_0_#735C00] flex items-center justify-center text-[#FFCC00]">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
            <div>
              <h3 className="font-mono text-sm font-bold text-[#F4F4F0] uppercase tracking-wide">
                PROCESSING TELEMETRY FILE [JOB #{activeAnalysisId}]
              </h3>
              <p className="font-mono text-xs text-[#9A9A91] mt-1 max-w-md mx-auto leading-relaxed">
                The backend detection pipeline is inspecting DNS queries, payload signatures, and API endpoints. Status is automatically refreshed every 3 seconds.
              </p>
            </div>
            <div className="inline-flex items-center gap-2 font-mono text-[11px] text-[#FFCC00] bg-[#0D0D0D] px-3 py-1.5 border border-[#333330]">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              <span>STATUS: {analysisResult?.status ? analysisResult.status.toUpperCase() : 'PENDING'}</span>
            </div>
          </div>
        </Card>
      )}


      {/* 3. Analysis Failed State */}
      {activeAnalysisId && isAnalysisFailed && (
        <QueryErrorState
          title={`Analysis Failed [Job ${activeAnalysisId}]`}
          error={{
            message:
              analysisResult?.errorMessage ||
              'Backend parser encountered an error processing this traffic capture.',
          }}
          onRetry={() => refetchAnalysis()}
          isRetrying={isFetchingAnalysis}
        />
      )}

      {/* 4. API Error Loading Analysis */}
      {activeAnalysisId && isAnalysisError && (
        <QueryErrorState
          title={`Unable to Retrieve Analysis #${activeAnalysisId}`}
          error={analysisError}
          onRetry={() => refetchAnalysis()}
          isRetrying={isFetchingAnalysis}
        />
      )}

      {/* 5. Analysis Completed: Summary & Metrics */}
      {activeAnalysisId && isAnalysisCompleted && analysisResult && (
        <div className="space-y-6">
          {/* Analysis Header Card */}
          <Card
            variant="charcoal"
            title="Analysis Summary & Telemetry Metadata"
            subtitle={`Analysis ID: ${analysisResult.analysisId} | File: ${
              analysisResult.original_filename || 'capture'
            } | Format: ${(analysisResult.file_format || 'auto').toUpperCase()} | Timestamp: ${
              analysisResult.completedAt || analysisResult.createdAt || analysisResult.timestamp || 'Not available'
            }`}
            headerIcon={<CheckCircle2 className="w-5 h-5 text-[#00E575]" />}
            action={
              <div className="flex items-center gap-2">
                <Badge variant="accent">
                  {(analysisResult.file_format || 'traffic').toUpperCase()}
                </Badge>
                <Button variant="outline" size="sm" onClick={handleReset}>
                  ANALYZE ANOTHER FILE
                </Button>
              </div>
            }
          >
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono text-xs">
                <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                  <span className="text-[#9A9A91] text-[10px] uppercase block">Total Records / Packets</span>
                  <span className="text-lg font-bold text-[#F4F4F0]">
                    {analysisResult.summary?.totalPackets ??
                      analysisResult.summary?.totalRecords ??
                      analysisResult.total_rows_received ??
                      analysisResult.totalRecords ??
                      analysisResult.records?.length ??
                      'Not available'}
                  </span>
                  {analysisResult.valid_rows !== undefined && (
                    <span className="text-[10px] text-[#00E575] block mt-0.5">
                      {analysisResult.valid_rows} valid flows parsed
                    </span>
                  )}
                </div>
                <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                  <span className="text-[#9A9A91] text-[10px] uppercase block">AI Flows Detected</span>
                  <span className="text-lg font-bold text-[#FFCC00]">
                    {analysisResult.summary?.aiFlowsDetected ?? 'Not available'}
                  </span>
                </div>
                <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                  <span className="text-[#9A9A91] text-[10px] uppercase block">Unique Providers</span>
                  <span className="text-lg font-bold text-[#F4F4F0]">
                    {analysisResult.summary?.uniqueProviders ?? 'Not available'}
                  </span>
                </div>
                <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                  <span className="text-[#9A9A91] text-[10px] uppercase block">High-Risk Flows</span>
                  <span className="text-lg font-bold text-[#FF6B6B]">
                    {analysisResult.summary?.highRiskFlows ?? 'Not available'}
                  </span>
                </div>
              </div>

              {/* Rejected / Truncated Packets Callout */}
              {Boolean(analysisResult.rejected_rows && analysisResult.rejected_rows > 0) && (
                <div className="p-3 bg-[#2A1C0A] border border-[#735C00] text-[#FFCC00] flex items-center gap-2.5 font-mono text-xs">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-[#FFCC00]" />
                  <span>
                    <strong>Capture Notice:</strong> {analysisResult.rejected_rows} packets or frames were rejected due to corruption, truncation, or malformed protocol headers. Valid traffic was processed safely.
                  </span>
                </div>
              )}
            </div>
          </Card>

          {/* Records Table Section */}
          <div className="space-y-4">
            {/* Filter and Search Bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 font-mono text-xs">
              <div className="relative flex-1 max-w-md">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#9A9A91]" />
                <input
                  type="text"
                  placeholder="SEARCH IP, DOMAIN, PROTOCOL..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full bg-[#171716] border border-[#333330] pl-9 pr-3 py-2 text-[#F4F4F0] font-mono text-xs focus:outline-none focus:border-[#FFCC00] placeholder:text-[#9A9A91]"
                />
              </div>

              <div className="flex items-center gap-2">
                <Filter className="w-3.5 h-3.5 text-[#9A9A91]" />
                <span className="text-[#9A9A91] text-[11px] uppercase">Filter:</span>
                <select
                  value={riskFilter}
                  onChange={(e) => {
                    setRiskFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="bg-[#171716] border border-[#333330] px-3 py-1.5 text-[#F4F4F0] font-mono text-xs focus:outline-none focus:border-[#FFCC00]"
                >
                  <option value="all">ALL CLASSIFICATIONS</option>
                  <option value="critical">CRITICAL</option>
                  <option value="high">HIGH</option>
                  <option value="medium">MEDIUM</option>
                  <option value="low">LOW</option>
                </select>
              </div>
            </div>

            {/* Records Table */}
            {filteredRecords.length === 0 ? (
              <EmptyState
                title="No Matching Records"
                description={
                  analysisResult.records?.length === 0
                    ? 'The analysis completed successfully, but 0 AI traffic flows or anomalous packets were identified in this capture file.'
                    : 'No traffic records matched the current search and classification filters.'
                }
                statusLabel="EMPTY RESULT SET"
                action={
                  <Button variant="secondary" size="sm" onClick={handleReset}>
                    ANALYZE ANOTHER FILE
                  </Button>
                }
              />
            ) : (
              <div className="border-2 border-[#333330] bg-[#171716] shadow-[4px_4px_0_#000000] overflow-x-auto">
                <table className="w-full border-collapse font-mono text-xs text-left">
                  <thead>
                    <tr className="bg-[#181818] border-b-2 border-[#333330] text-[#FFCC00]">
                      <th className="py-3 px-3 uppercase tracking-wider">Timestamp</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Source IP</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Destination Domain / IP</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Port</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Protocol</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Bytes Sent</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Bytes Recv</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Classification</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Evidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#333330]">
                    {paginatedRecords.map((item, index) => {
                      const destDisplay =
                        item.destinationHost ||
                        item.destinationDomain ||
                        item.destination_domain ||
                        item.destinationIp ||
                        item.destination_ip ||
                        item.sni_hostname ||
                        'Not available';

                      const sourceDisplay =
                        item.sourceIp ||
                        item.source_ip ||
                        'Not available';

                      const portDisplay =
                        item.destinationPort !== undefined
                          ? item.destinationPort
                          : item.destination_port !== undefined
                          ? item.destination_port
                          : item.port !== undefined
                          ? item.port
                          : 'Not available';

                      const bytesSentVal = item.bytesSent ?? item.bytes_sent;
                      const bytesRecvVal = item.bytesReceived ?? item.bytes_received;

                      const evidenceDisplay = item.detectionEvidence
                        ? Array.isArray(item.detectionEvidence)
                          ? item.detectionEvidence.join(', ')
                          : item.detectionEvidence
                        : item.evidence
                        ? Array.isArray(item.evidence)
                          ? item.evidence.join(', ')
                          : item.evidence
                        : item.sni_hostname || item.http_uri || 'Not available';

                      const classificationDisplay =
                        item.classification || item.riskLevel || item.risk_level || 'Not available';

                      return (
                        <tr
                          key={item.id || `record-${index}`}
                          className="hover:bg-[#1E1E1C] transition-colors"
                        >
                          <td className="py-2.5 px-3 text-[#9A9A91] whitespace-nowrap">
                            {item.timestamp || 'Not available'}
                          </td>
                          <td className="py-2.5 px-3 text-[#F4F4F0] font-bold whitespace-nowrap">
                            {sourceDisplay}
                          </td>
                          <td className="py-2.5 px-3 text-[#FFCC00]">
                            {destDisplay}
                          </td>
                          <td className="py-2.5 px-3 text-[#F4F4F0]">
                            {portDisplay}
                          </td>
                          <td className="py-2.5 px-3">
                            {item.protocol ? (
                              <Badge variant="muted" size="sm">{item.protocol}</Badge>
                            ) : (
                              <span className="text-[#9A9A91]">Not available</span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-[#9A9A91]">
                            {bytesSentVal !== undefined ? `${bytesSentVal.toLocaleString()} B` : 'Not available'}
                          </td>
                          <td className="py-2.5 px-3 text-[#9A9A91]">
                            {bytesRecvVal !== undefined ? `${bytesRecvVal.toLocaleString()} B` : 'Not available'}
                          </td>
                          <td className="py-2.5 px-3">
                            {classificationDisplay !== 'Not available' ? (
                              <Badge
                                size="sm"
                                variant={
                                  classificationDisplay.toLowerCase() === 'high' ||
                                  classificationDisplay.toLowerCase() === 'critical'
                                    ? 'danger'
                                    : classificationDisplay.toLowerCase() === 'medium'
                                    ? 'warning'
                                    : 'default'
                                }
                              >
                                {classificationDisplay}
                              </Badge>
                            ) : (
                              <span className="text-[#9A9A91]">Not available</span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-[11px] text-[#9A9A91] max-w-[220px] truncate" title={evidenceDisplay}>
                            {evidenceDisplay}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>

                {/* Pagination Controls */}
                <div className="p-3 bg-[#181818] border-t border-[#333330] flex items-center justify-between font-mono text-xs">
                  <div className="text-[#9A9A91]">
                    Showing {(currentPage - 1) * pageSize + 1} to{' '}
                    {Math.min(currentPage * pageSize, filteredRecords.length)} of{' '}
                    {filteredRecords.length} records
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      icon={<ChevronLeft className="w-3.5 h-3.5" />}
                    >
                      PREV
                    </Button>
                    <span className="px-2 text-[#F4F4F0]">
                      {currentPage} / {totalPages}
                    </span>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      icon={<ChevronRight className="w-3.5 h-3.5" />}
                    >
                      NEXT
                    </Button>
                  </div>
                </div>

                {/* Measurement Semantics Footnote */}
                <div className="px-4 py-2.5 bg-[#121212] border-t border-[#262624] text-[10px] text-[#7A7A72] flex flex-col sm:flex-row sm:items-center justify-between gap-1 font-mono">
                  <span>* Wire Byte Counts: Measured as total Layer 3 IP datagram length (IP/TCP headers + payload) on network interface.</span>
                  <span>TLS confidentiality preserved; encrypted payloads do not reveal prompt contents or token costs.</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 6. Default Empty State (No file selected, awaiting file upload) */}
      {!activeAnalysisId && !selectedFile && (
        <EmptyState
          title="No Active Traffic Analysis"
          description="Upload a CSV or JSON network capture file above to initiate deep inspection of outbound AI connections."
          statusLabel="STANDBY"
          icon={<ShieldAlert className="w-7 h-7" />}
          action={
            <Button
              variant="secondary"
              size="md"
              icon={<Upload className="w-3.5 h-3.5" />}
              onClick={() => fileInputRef.current?.click()}
            >
              SELECT TRAFFIC FILE
            </Button>
          }
        />
      )}
    </PageContainer>
  );
};
