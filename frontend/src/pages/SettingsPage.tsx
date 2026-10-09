import React, { useState, useMemo } from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { LoadingState } from '../components/common/LoadingState';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { useApiHealth } from '../hooks/useApiHealth';
import {
  usePolicies,
  usePolicySummary,
  useUpdatePolicyStatus,
  useDisablePolicy,
} from '../hooks/usePolicies';
import {
  getEffectiveAdminToken,
  setStoredAdminToken,
} from '../api/policies';
import { PolicyFormModal } from '../components/governance/PolicyFormModal';
import { PolicyConfirmModal } from '../components/governance/PolicyConfirmModal';
import { PolicyAuditLogDrawer } from '../components/governance/PolicyAuditLogDrawer';
import type { AIGovernancePolicy } from '../types';
import { API_BASE_URL } from '../lib/config';
import {
  Server,
  ShieldCheck,
  ShieldAlert,
  ShieldOff,
  Plus,
  RefreshCw,
  Search,
  Key,
  History,
  Edit2,
  CheckCircle2,
  Eye,
  EyeOff,
  Ban,
  Check,
  AlertCircle,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  // 1. API Health (retained for backend diagnostics and test compatibility)
  const { refetch: refetchHealth, isFetching: isFetchingHealth } = useApiHealth();

  // 2. Admin Token state
  const [adminToken, setAdminToken] = useState<string>(() => getEffectiveAdminToken());
  const [showToken, setShowToken] = useState(false);
  const [tokenSavedMessage, setTokenSavedMessage] = useState<string | null>(null);

  const handleSaveToken = (newToken: string) => {
    setAdminToken(newToken);
    setStoredAdminToken(newToken);
    setTokenSavedMessage('Administrative authorization token updated.');
    setTimeout(() => setTokenSavedMessage(null), 3000);
  };

  // 3. Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'APPROVED' | 'BLOCKED' | 'DISABLED'>('ALL');

  // 4. Governance Policies Query
  const {
    data: policies,
    isLoading: isLoadingPolicies,
    isError: isErrorPolicies,
    error: policiesError,
    refetch: refetchPolicies,
    isFetching: isFetchingPolicies,
  } = usePolicies();

  const { data: summaryMetrics } = usePolicySummary();

  // 5. Mutations
  const updateStatusMutation = useUpdatePolicyStatus();
  const disableMutation = useDisablePolicy();

  // 6. Modal States
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [policyToEdit, setPolicyToEdit] = useState<AIGovernancePolicy | null>(null);

  const [confirmModalConfig, setConfirmModalConfig] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    confirmVariant?: 'primary' | 'danger' | 'secondary';
    onConfirm: (notes?: string) => Promise<void>;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: async () => {},
  });

  const [isAuditDrawerOpen, setIsAuditDrawerOpen] = useState(false);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  const showSuccess = (msg: string) => {
    setSuccessBanner(msg);
    setErrorBanner(null);
    setTimeout(() => setSuccessBanner(null), 5000);
  };

  const showError = (msg: string) => {
    setErrorBanner(msg);
    setSuccessBanner(null);
    setTimeout(() => setErrorBanner(null), 5000);
  };

  // 7. Filtered Policies
  const filteredPolicies = useMemo(() => {
    if (!policies) return [];
    return policies.filter((p) => {
      const name = (p.providerName || p.provider_name || '').toLowerCase();
      const rule = (p.policyRule || p.policy_rule || '').toLowerCase();
      const desc = (p.description || '').toLowerCase();
      const sigs = (p.domainSignatures || p.domain_signatures || []).join(' ').toLowerCase();
      const q = searchQuery.toLowerCase().trim();

      const matchesSearch = !q || name.includes(q) || rule.includes(q) || desc.includes(q) || sigs.includes(q);
      if (!matchesSearch) return false;

      const isEnabled = p.isEnabled ?? p.is_enabled ?? true;
      const status = (p.approvalStatus || p.approval_status || 'approved').toLowerCase();

      if (statusFilter === 'DISABLED') return !isEnabled;
      if (!isEnabled) return statusFilter === 'ALL';

      if (statusFilter === 'APPROVED') return status === 'approved';
      if (statusFilter === 'BLOCKED') return status === 'unapproved' || status === 'blocked' || status === 'restricted';

      return true;
    });
  }, [policies, searchQuery, statusFilter]);

  // 8. Action Handlers with Confirmation
  const handleToggleStatus = (policy: AIGovernancePolicy) => {
    const isCurrentlyApproved =
      (policy.approvalStatus || policy.approval_status || '').toLowerCase() === 'approved';
    const targetStatus = isCurrentlyApproved ? 'blocked' : 'approved';
    const provider = policy.providerName || policy.provider_name || 'Provider';

    setConfirmModalConfig({
      isOpen: true,
      title: isCurrentlyApproved ? `Revoke Approval: ${provider}` : `Authorize Provider: ${provider}`,
      message: isCurrentlyApproved
        ? `Are you sure you want to block and classify "${provider}" as unauthorized Shadow AI? Network traffic directed to this provider will trigger risk violations.`
        : `Are you sure you want to approve "${provider}" for organizational business use? Traffic compliance penalties will be cleared.`,
      confirmText: isCurrentlyApproved ? 'BLOCK PROVIDER' : 'AUTHORIZE PROVIDER',
      confirmVariant: isCurrentlyApproved ? 'danger' : 'primary',
      onConfirm: async (notes) => {
        try {
          await updateStatusMutation.mutateAsync({
            policyId: policy.id,
            approvalStatus: targetStatus,
            notes,
            token: adminToken,
          });
          showSuccess(`Approval status for "${provider}" updated to "${targetStatus}".`);
          setConfirmModalConfig((prev) => ({ ...prev, isOpen: false }));
        } catch (err: any) {
          showError(err?.message || 'Failed to update approval status.');
        }
      },
    });
  };

  const handleDisablePolicy = (policy: AIGovernancePolicy) => {
    const provider = policy.providerName || policy.provider_name || 'Provider';
    setConfirmModalConfig({
      isOpen: true,
      title: `Disable Policy: ${provider}`,
      message: `Are you sure you want to disable the governance policy for "${provider}"? Disabled rules are safely skipped during traffic evaluations.`,
      confirmText: 'DISABLE RULE',
      confirmVariant: 'danger',
      onConfirm: async () => {
        try {
          await disableMutation.mutateAsync({
            policyId: policy.id,
            token: adminToken,
          });
          showSuccess(`Policy for "${provider}" has been disabled.`);
          setConfirmModalConfig((prev) => ({ ...prev, isOpen: false }));
        } catch (err: any) {
          showError(err?.message || 'Failed to disable policy.');
        }
      },
    });
  };

  // Sanitized API URL display
  const sanitizedApiUrl = useMemo(() => {
    try {
      const parsed = new URL(API_BASE_URL);
      return `${parsed.protocol}//${parsed.host}${parsed.pathname}`;
    } catch {
      return API_BASE_URL;
    }
  }, []);

  return (
    <PageContainer
      title="Settings"
      description="Manage database-backed enterprise AI governance policies, approved and blocked provider registries, and client API communication bindings."
      badge={<Badge variant="accent">GOVERNANCE ADMIN</Badge>}
    >
      <div className="space-y-6">
        {/* Success and Error Notification Banners */}
        {successBanner && (
          <div className="p-3 bg-[#00E575]/10 border-2 border-[#00E575] text-[#00E575] font-mono text-xs flex items-center justify-between shadow-[3px_3px_0_#004D26]">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successBanner}</span>
            </div>
            <Button variant="outline" size="sm" onClick={() => setSuccessBanner(null)}>
              DISMISS
            </Button>
          </div>
        )}

        {errorBanner && (
          <div className="p-3 bg-[#FF4D4D]/10 border-2 border-[#FF4D4D] text-[#FF6B6B] font-mono text-xs flex items-center justify-between shadow-[3px_3px_0_#4D0000]">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorBanner}</span>
            </div>
            <Button variant="outline" size="sm" onClick={() => setErrorBanner(null)}>
              DISMISS
            </Button>
          </div>
        )}

        {/* 1. Admin Authentication Bar */}
        <Card
          variant="charcoal"
          title="Administrative Authorization"
          subtitle="Enterprise governance mutations require valid administrative authorization headers."
          headerIcon={<Key className="w-5 h-5 text-[#FFCC00]" />}
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsAuditDrawerOpen(true)}
              icon={<History className="w-3.5 h-3.5" />}
            >
              VIEW AUDIT TRAIL
            </Button>
          }
        >
          <div className="space-y-3 font-mono text-xs">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <div className="flex-1 w-full relative">
                <input
                  type={showToken ? 'text' : 'password'}
                  value={adminToken}
                  onChange={(e) => handleSaveToken(e.target.value)}
                  placeholder="Enter administrator authorization key (X-Admin-Token)"
                  className="w-full bg-[#0D0D0D] border border-[#333330] px-3 py-2 pr-10 text-[#F4F4F0] font-mono text-xs outline-none focus:border-[#FFCC00]"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#9A9A91] hover:text-[#F4F4F0]"
                >
                  {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <Badge variant="success" size="sm" icon={<ShieldCheck className="w-3.5 h-3.5" />}>
                ADMIN AUTH ACTIVE
              </Badge>
            </div>
            {tokenSavedMessage && (
              <p className="text-[10px] text-[#00E575]">{tokenSavedMessage}</p>
            )}
            <p className="text-[10px] text-[#9A9A91]">
              Token is sent as <code className="text-[#FFCC00]">X-Admin-Token</code> on all policy creation, update, approval toggle, and disable requests.
            </p>
          </div>
        </Card>

        {/* 2. Policy Summary KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card variant="charcoal">
            <div className="space-y-1">
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#9A9A91]">
                Total Policies
              </div>
              <div className="text-2xl font-bold font-mono text-[#F4F4F0]">
                {summaryMetrics?.totalPolicies ?? summaryMetrics?.total_policies ?? policies?.length ?? 0}
              </div>
              <div className="text-[10px] text-[#666660]">Database-governed rules</div>
            </div>
          </Card>

          <Card variant="charcoal">
            <div className="space-y-1">
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#00E575] flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Approved Providers
              </div>
              <div className="text-2xl font-bold font-mono text-[#00E575]">
                {summaryMetrics?.approvedPolicies ?? summaryMetrics?.approved_policies ?? 0}
              </div>
              <div className="text-[10px] text-[#666660]">Enterprise sanctioned</div>
            </div>
          </Card>

          <Card variant="charcoal">
            <div className="space-y-1">
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#FF6B6B] flex items-center gap-1">
                <ShieldAlert className="w-3.5 h-3.5" />
                Blocked / Shadow
              </div>
              <div className="text-2xl font-bold font-mono text-[#FF6B6B]">
                {summaryMetrics?.unapprovedPolicies ?? summaryMetrics?.unapproved_policies ?? 0}
              </div>
              <div className="text-[10px] text-[#666660]">Prohibited AI access</div>
            </div>
          </Card>

          <Card variant="charcoal">
            <div className="space-y-1">
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#9A9A91] flex items-center gap-1">
                <ShieldOff className="w-3.5 h-3.5" />
                Disabled Rules
              </div>
              <div className="text-2xl font-bold font-mono text-[#9A9A91]">
                {summaryMetrics?.disabledPolicies ?? summaryMetrics?.disabled_policies ?? 0}
              </div>
              <div className="text-[10px] text-[#666660]">Inactive governance</div>
            </div>
          </Card>
        </div>

        {/* 3. Action Toolbar & Filter */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[#171716] p-3 border-2 border-[#333330]">
          <div className="flex flex-1 items-center gap-2 bg-[#0D0D0D] border border-[#333330] px-3 py-1.5">
            <Search className="w-4 h-4 text-[#9A9A91] shrink-0" />
            <input
              type="text"
              placeholder="Search policies by provider, domain, or rule..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-[#F4F4F0] font-mono text-xs w-full outline-none placeholder-[#666660]"
            />
          </div>

          {/* Filter Status Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto">
            {(['ALL', 'APPROVED', 'BLOCKED', 'DISABLED'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setStatusFilter(tab)}
                className={`px-2.5 py-1 text-[11px] font-mono font-bold uppercase transition-colors border ${
                  statusFilter === tab
                    ? 'bg-[#FFCC00] text-[#0D0D0D] border-[#FFCC00]'
                    : 'bg-[#181818] text-[#9A9A91] border-[#333330] hover:text-[#F4F4F0]'
                }`}
              >
                {tab}
              </button>
            ))}

            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setPolicyToEdit(null);
                setIsFormModalOpen(true);
              }}
              icon={<Plus className="w-3.5 h-3.5" />}
            >
              REGISTER POLICY
            </Button>
          </div>
        </div>

        {/* 4. Policy Management Table */}
        <Card
          variant="charcoal"
          title="Enterprise AI Provider Governance Policies"
          subtitle="Deterministic evaluation engine matches observed network traffic against active database policies. Unapproved or blocked policies strictly override approvals."
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchPolicies()}
              disabled={isFetchingPolicies}
              icon={<RefreshCw className={`w-3.5 h-3.5 ${isFetchingPolicies ? 'animate-spin' : ''}`} />}
            >
              REFRESH
            </Button>
          }
        >
          {isLoadingPolicies ? (
            <LoadingState message="Loading governance policies from database..." />
          ) : isErrorPolicies ? (
            <QueryErrorState error={policiesError} onRetry={() => refetchPolicies()} />
          ) : filteredPolicies.length === 0 ? (
            <EmptyState
              title="No AI governance policies found"
              description={
                searchQuery || statusFilter !== 'ALL'
                  ? 'No policies match the active filter criteria. Try clearing search.'
                  : 'No policies registered yet. Click "Register Policy" to configure your first provider.'
              }
              action={
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setSearchQuery('');
                    setStatusFilter('ALL');
                    setPolicyToEdit(null);
                    setIsFormModalOpen(true);
                  }}
                  icon={<Plus className="w-3.5 h-3.5" />}
                >
                  ADD FIRST POLICY
                </Button>
              }
            />
          ) : (
            <div className="overflow-x-auto -mx-4 -mb-4">
              <table className="w-full border-collapse font-mono text-xs text-left">
                <thead>
                  <tr className="bg-[#181818] border-y border-[#333330] text-[#FFCC00]">
                    <th className="py-2.5 px-4 font-bold uppercase">Provider & ID</th>
                    <th className="py-2.5 px-4 font-bold uppercase">Domain Signatures</th>
                    <th className="py-2.5 px-4 font-bold uppercase">Approval Status</th>
                    <th className="py-2.5 px-4 font-bold uppercase">Policy Rule & Description</th>
                    <th className="py-2.5 px-4 font-bold uppercase text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#222220]">
                  {filteredPolicies.map((p) => {
                    const isEnabled = p.isEnabled ?? p.is_enabled ?? true;
                    const statusStr = (p.approvalStatus || p.approval_status || 'approved').toLowerCase();
                    const isApproved = statusStr === 'approved';
                    const provider = p.providerName || p.provider_name || 'Unknown Provider';
                    const externalId = p.externalId || p.external_id || '';
                    const domainSigs = p.domainSignatures || p.domain_signatures || [];
                    const ruleCode = p.policyRule || p.policy_rule || '';

                    return (
                      <tr
                        key={p.id}
                        className={`hover:bg-[#1C1C1B] transition-colors ${
                          !isEnabled ? 'opacity-60 bg-[#121212]' : ''
                        }`}
                      >
                        {/* Provider & ID */}
                        <td className="py-3 px-4">
                          <div className="font-bold text-[#F4F4F0] text-sm">{provider}</div>
                          <div className="text-[10px] text-[#666660] font-mono">{externalId}</div>
                        </td>

                        {/* Domain Signatures */}
                        <td className="py-3 px-4 max-w-xs">
                          {domainSigs.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {domainSigs.map((sig) => (
                                <span
                                  key={sig}
                                  className="px-1.5 py-0.5 bg-[#0D0D0D] border border-[#333330] text-[10px] text-[#CACAC4]"
                                >
                                  {sig}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-[10px] text-[#666660]">Any matching endpoint</span>
                          )}
                        </td>

                        {/* Approval Status */}
                        <td className="py-3 px-4">
                          {!isEnabled ? (
                            <Badge variant="muted" size="sm" icon={<ShieldOff className="w-3 h-3" />}>
                              DISABLED
                            </Badge>
                          ) : isApproved ? (
                            <Badge variant="success" size="sm" icon={<ShieldCheck className="w-3 h-3" />}>
                              APPROVED
                            </Badge>
                          ) : (
                            <Badge variant="danger" size="sm" icon={<ShieldAlert className="w-3 h-3" />}>
                              BLOCKED / SHADOW
                            </Badge>
                          )}
                        </td>

                        {/* Policy Rule & Description */}
                        <td className="py-3 px-4 max-w-sm">
                          <div className="text-[11px] font-semibold text-[#F4F4F0]">{ruleCode}</div>
                          {p.description && (
                            <div className="text-[10px] text-[#9A9A91] line-clamp-2 mt-0.5">
                              {p.description}
                            </div>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="py-3 px-4 text-right">
                          <div className="inline-flex items-center gap-1.5">
                            {/* Toggle Approval Button */}
                            <Button
                              variant={isApproved ? 'danger' : 'primary'}
                              size="sm"
                              onClick={() => handleToggleStatus(p)}
                              icon={isApproved ? <Ban className="w-3 h-3" /> : <Check className="w-3 h-3" />}
                            >
                              {isApproved ? 'BLOCK' : 'APPROVE'}
                            </Button>

                            {/* Edit Button */}
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => {
                                setPolicyToEdit(p);
                                setIsFormModalOpen(true);
                              }}
                              icon={<Edit2 className="w-3 h-3" />}
                            >
                              EDIT
                            </Button>

                            {/* Disable Button */}
                            {isEnabled && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDisablePolicy(p)}
                              >
                                DISABLE
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* 5. API Connectivity & Backend Binding (Retained for test compatibility & diagnostics) */}
        <Card
          variant="charcoal"
          title="Backend Ingestion Binding"
          subtitle="Target URL used for REST queries, live packet telemetry, and status probes."
          headerIcon={<Server className="w-5 h-5 text-[#FFCC00]" />}
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => refetchHealth()}
              disabled={isFetchingHealth}
              icon={<RefreshCw className={`w-3.5 h-3.5 ${isFetchingHealth ? 'animate-spin' : ''}`} />}
            >
              RETEST CONNECTION
            </Button>
          }
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="space-y-1.5">
              <label className="text-[#9A9A91] text-[10px] uppercase tracking-wider block">
                Configured Backend Endpoint (VITE_API_BASE_URL)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  readOnly
                  value={sanitizedApiUrl}
                  className="flex-1 bg-[#0D0D0D] border border-[#333330] px-3 py-2 text-[#F4F4F0] font-mono text-xs select-all outline-none focus:border-[#FFCC00]"
                />
                <Badge variant="accent" size="sm">
                  PORT 8000
                </Badge>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Modals & Drawers */}
      <PolicyFormModal
        isOpen={isFormModalOpen}
        policyToEdit={policyToEdit}
        onClose={() => {
          setIsFormModalOpen(false);
          setPolicyToEdit(null);
        }}
        onSuccess={(msg) => showSuccess(msg)}
      />

      <PolicyConfirmModal
        isOpen={confirmModalConfig.isOpen}
        title={confirmModalConfig.title}
        message={confirmModalConfig.message}
        confirmText={confirmModalConfig.confirmText}
        confirmVariant={confirmModalConfig.confirmVariant}
        onConfirm={confirmModalConfig.onConfirm}
        onClose={() => setConfirmModalConfig((prev) => ({ ...prev, isOpen: false }))}
      />

      <PolicyAuditLogDrawer
        isOpen={isAuditDrawerOpen}
        onClose={() => setIsAuditDrawerOpen(false)}
      />
    </PageContainer>
  );
};
