import React, { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import { useCreatePolicy, useUpdatePolicy } from '../../hooks/usePolicies';
import type { AIGovernancePolicy, PolicyApprovalStatus } from '../../types';
import { X, ShieldCheck, ShieldAlert, Loader2, Plus, Edit2 } from 'lucide-react';

export interface PolicyFormModalProps {
  isOpen: boolean;
  policyToEdit: AIGovernancePolicy | null;
  onClose: () => void;
  onSuccess: (message: string) => void;
}

export const PolicyFormModal: React.FC<PolicyFormModalProps> = ({
  isOpen,
  policyToEdit,
  onClose,
  onSuccess,
}) => {
  const isEditing = Boolean(policyToEdit);

  const [providerName, setProviderName] = useState('');
  const [domainSignaturesText, setDomainSignaturesText] = useState('');
  const [approvalStatus, setApprovalStatus] = useState<PolicyApprovalStatus>('approved');
  const [isEnabled, setIsEnabled] = useState(true);
  const [policyRule, setPolicyRule] = useState('');
  const [description, setDescription] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  const createMutation = useCreatePolicy();
  const updateMutation = useUpdatePolicy();
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  useEffect(() => {
    if (policyToEdit) {
      setProviderName(policyToEdit.providerName || policyToEdit.provider_name || '');
      const sigs = policyToEdit.domainSignatures || policyToEdit.domain_signatures || [];
      setDomainSignaturesText(sigs.join(', '));
      const status = (policyToEdit.approvalStatus || policyToEdit.approval_status || 'approved') as PolicyApprovalStatus;
      setApprovalStatus(status);
      setIsEnabled(policyToEdit.isEnabled ?? policyToEdit.is_enabled ?? true);
      setPolicyRule(policyToEdit.policyRule || policyToEdit.policy_rule || '');
      setDescription(policyToEdit.description || '');
    } else {
      setProviderName('');
      setDomainSignaturesText('');
      setApprovalStatus('approved');
      setIsEnabled(true);
      setPolicyRule('');
      setDescription('');
    }
    setValidationError(null);
    setBackendError(null);
  }, [policyToEdit, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setBackendError(null);

    const cleanName = providerName.trim();
    if (cleanName.length < 2) {
      setValidationError('Provider name must be at least 2 characters long.');
      return;
    }

    const rawDomains = domainSignaturesText
      .split(/[,\n]/)
      .map((d) => d.trim().toLowerCase())
      .filter((d) => d.length > 0);

    // Sanitize domain hostnames client-side as well
    const domainSignatures = Array.from(
      new Set(
        rawDomains.map((d) => {
          let s = d;
          if (s.startsWith('http://')) s = s.slice(7);
          else if (s.startsWith('https://')) s = s.slice(8);
          return s.split('/')[0].split(':')[0];
        }).filter((d) => d.length > 0)
      )
    );

    const defaultRule =
      approvalStatus === 'approved'
        ? 'POLICY-AI-00: Approved Enterprise Provider'
        : 'POLICY-AI-01: Prohibited Shadow AI Provider';

    try {
      if (isEditing && policyToEdit) {
        await updateMutation.mutateAsync({
          policyId: policyToEdit.id,
          payload: {
            provider_name: cleanName,
            domain_signatures: domainSignatures,
            approval_status: approvalStatus,
            is_enabled: isEnabled,
            policy_rule: policyRule.trim() || defaultRule,
            description: description.trim() || undefined,
          },
        });
        onSuccess(`Policy for "${cleanName}" was updated successfully.`);
      } else {
        await createMutation.mutateAsync({
          payload: {
            provider_name: cleanName,
            domain_signatures: domainSignatures,
            approval_status: approvalStatus,
            is_enabled: isEnabled,
            policy_rule: policyRule.trim() || defaultRule,
            description: description.trim() || undefined,
          },
        });
        onSuccess(`Governance policy for "${cleanName}" created successfully.`);
      }
      onClose();
    } catch (err: any) {
      const msg = err?.message || err?.detail || 'An unexpected error occurred while saving policy.';
      setBackendError(msg);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#000000]/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-xl border-2 border-[#333330] bg-[#121212] shadow-[8px_8px_0_#000000] max-h-[90vh] flex flex-col font-mono text-xs">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b-2 border-[#333330] bg-[#181818]">
          <div className="flex items-center gap-2">
            {isEditing ? (
              <Edit2 className="w-4 h-4 text-[#FFCC00]" />
            ) : (
              <Plus className="w-4 h-4 text-[#FFCC00]" />
            )}
            <h3 className="font-bold text-[#F4F4F0] uppercase tracking-wider text-sm">
              {isEditing ? 'Edit AI Governance Policy' : 'Register AI Provider Policy'}
            </h3>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="text-[#9A9A91] hover:text-[#F4F4F0] p-1 border border-transparent hover:border-[#333330] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 overflow-y-auto flex-1">
          {validationError && (
            <div className="p-3 bg-[#FF4D4D]/10 border border-[#8C2323] text-[#FF6B6B] flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{validationError}</span>
            </div>
          )}

          {backendError && (
            <div className="p-3 bg-[#FF4D4D]/10 border border-[#8C2323] text-[#FF6B6B] flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{backendError}</span>
            </div>
          )}

          {/* Provider Name */}
          <div className="space-y-1.5">
            <label className="text-[#9A9A91] text-[10px] uppercase tracking-wider block font-bold">
              AI Provider Name <span className="text-[#FF4D4D]">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. OpenAI, Anthropic, Mistral, Cohere"
              value={providerName}
              onChange={(e) => setProviderName(e.target.value)}
              disabled={isSubmitting}
              className="w-full bg-[#0D0D0D] border border-[#333330] px-3 py-2 text-[#F4F4F0] placeholder-[#666660] outline-none focus:border-[#FFCC00]"
              required
            />
          </div>

          {/* Domain Signatures */}
          <div className="space-y-1.5">
            <label className="text-[#9A9A91] text-[10px] uppercase tracking-wider block font-bold">
              Domain / Endpoint Signatures (Comma-separated)
            </label>
            <input
              type="text"
              placeholder="e.g. api.openai.com, chatgpt.com, openai.com"
              value={domainSignaturesText}
              onChange={(e) => setDomainSignaturesText(e.target.value)}
              disabled={isSubmitting}
              className="w-full bg-[#0D0D0D] border border-[#333330] px-3 py-2 text-[#F4F4F0] placeholder-[#666660] outline-none focus:border-[#FFCC00]"
            />
            <p className="text-[10px] text-[#666660]">
              Network traffic matching these destination hosts will inherit this policy rule.
            </p>
          </div>

          {/* Approval Status */}
          <div className="space-y-1.5">
            <label className="text-[#9A9A91] text-[10px] uppercase tracking-wider block font-bold">
              Enterprise Approval Verdict <span className="text-[#FF4D4D]">*</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label
                className={`flex items-center gap-2.5 p-3 border cursor-pointer transition-colors ${
                  approvalStatus === 'approved'
                    ? 'border-[#00E575] bg-[#00E575]/10 text-[#00E575]'
                    : 'border-[#333330] bg-[#0D0D0D] text-[#9A9A91] hover:border-[#666660]'
                }`}
              >
                <input
                  type="radio"
                  name="approval_status"
                  value="approved"
                  checked={approvalStatus === 'approved'}
                  onChange={() => setApprovalStatus('approved')}
                  disabled={isSubmitting}
                  className="accent-[#00E575]"
                />
                <ShieldCheck className="w-4 h-4 shrink-0" />
                <div>
                  <div className="font-bold uppercase text-xs">Approved Provider</div>
                  <div className="text-[10px] opacity-80">Authorized for business use</div>
                </div>
              </label>

              <label
                className={`flex items-center gap-2.5 p-3 border cursor-pointer transition-colors ${
                  approvalStatus === 'blocked' || approvalStatus === 'unapproved'
                    ? 'border-[#FF4D4D] bg-[#FF4D4D]/10 text-[#FF6B6B]'
                    : 'border-[#333330] bg-[#0D0D0D] text-[#9A9A91] hover:border-[#666660]'
                }`}
              >
                <input
                  type="radio"
                  name="approval_status"
                  value="blocked"
                  checked={approvalStatus === 'blocked' || approvalStatus === 'unapproved'}
                  onChange={() => setApprovalStatus('blocked')}
                  disabled={isSubmitting}
                  className="accent-[#FF4D4D]"
                />
                <ShieldAlert className="w-4 h-4 shrink-0" />
                <div>
                  <div className="font-bold uppercase text-xs">Blocked / Shadow AI</div>
                  <div className="text-[10px] opacity-80">Flags high/critical security risk</div>
                </div>
              </label>
            </div>
          </div>

          {/* Policy Rule Tag */}
          <div className="space-y-1.5">
            <label className="text-[#9A9A91] text-[10px] uppercase tracking-wider block font-bold">
              Policy Rule Code / Reference
            </label>
            <input
              type="text"
              placeholder={
                approvalStatus === 'approved'
                  ? 'POLICY-AI-00: Approved Enterprise Provider'
                  : 'POLICY-AI-01: Prohibited Shadow AI Provider'
              }
              value={policyRule}
              onChange={(e) => setPolicyRule(e.target.value)}
              disabled={isSubmitting}
              className="w-full bg-[#0D0D0D] border border-[#333330] px-3 py-2 text-[#F4F4F0] placeholder-[#666660] outline-none focus:border-[#FFCC00]"
            />
          </div>

          {/* Description & Business Justification */}
          <div className="space-y-1.5">
            <label className="text-[#9A9A91] text-[10px] uppercase tracking-wider block font-bold">
              Governance Description & Business Justification
            </label>
            <textarea
              rows={3}
              placeholder="e.g. Enterprise license agreement active with data privacy addendum (BAA/DPA)."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={isSubmitting}
              className="w-full bg-[#0D0D0D] border border-[#333330] px-3 py-2 text-[#F4F4F0] placeholder-[#666660] outline-none focus:border-[#FFCC00] resize-none"
            />
          </div>

          {/* Policy Active Switch */}
          <div className="flex items-center justify-between p-3 bg-[#0D0D0D] border border-[#333330]">
            <div>
              <span className="font-bold text-[#F4F4F0] uppercase block">Rule Active Status</span>
              <span className="text-[10px] text-[#9A9A91]">
                Disabled rules are skipped during network traffic analysis.
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={isEnabled}
                onChange={(e) => setIsEnabled(e.target.checked)}
                disabled={isSubmitting}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-[#333330] peer-focus:outline-none rounded-none peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[#0D0D0D] after:border-2 after:border-[#333330] after:h-5 after:w-5 after:transition-all peer-checked:bg-[#FFCC00] peer-checked:after:bg-[#0D0D0D]"></div>
            </label>
          </div>

          {/* Modal Footer */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#333330]">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={isSubmitting}
            >
              CANCEL
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={isSubmitting}
              icon={isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : undefined}
            >
              {isSubmitting
                ? 'SAVING...'
                : isEditing
                ? 'UPDATE POLICY'
                : 'CREATE POLICY'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
