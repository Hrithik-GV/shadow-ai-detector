import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { SettingsPage } from '../pages/SettingsPage';
import * as policiesApi from '../api/policies';
import type { AIGovernancePolicy, PolicySummaryMetrics } from '../types';

const mockPolicies: AIGovernancePolicy[] = [
  {
    id: '11111111-1111-1111-1111-111111111111',
    externalId: 'POL-OPENAI-001',
    external_id: 'POL-OPENAI-001',
    providerName: 'OpenAI',
    provider_name: 'OpenAI',
    domainSignatures: ['api.openai.com', 'chatgpt.com'],
    domain_signatures: ['api.openai.com', 'chatgpt.com'],
    approvalStatus: 'approved',
    approval_status: 'approved',
    isApproved: true,
    is_approved: true,
    isEnabled: true,
    is_enabled: true,
    policyRule: 'POLICY-AI-00: Approved Enterprise Provider',
    description: 'Corporate enterprise-wide approved LLM provider.',
    createdBy: 'admin',
    updatedBy: 'admin',
    createdAt: '2026-10-10T00:00:00Z',
    updatedAt: '2026-10-10T00:00:00Z',
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    externalId: 'POL-ANTHROPIC-002',
    external_id: 'POL-ANTHROPIC-002',
    providerName: 'Anthropic',
    provider_name: 'Anthropic',
    domainSignatures: ['api.anthropic.com', 'claude.ai'],
    domain_signatures: ['api.anthropic.com', 'claude.ai'],
    approvalStatus: 'blocked',
    approval_status: 'blocked',
    isApproved: false,
    is_approved: false,
    isEnabled: true,
    is_enabled: true,
    policyRule: 'POLICY-AI-01: Prohibited Shadow AI Provider',
    description: 'Direct consumer chat interface prohibited without security waiver.',
    createdBy: 'admin',
    updatedBy: 'admin',
    createdAt: '2026-10-10T00:00:00Z',
    updatedAt: '2026-10-10T00:00:00Z',
  },
];

const mockSummary: PolicySummaryMetrics = {
  totalPolicies: 2,
  approvedPolicies: 1,
  unapprovedPolicies: 1,
  disabledPolicies: 0,
  activeApprovedProviders: ['OpenAI'],
};

function renderSettingsPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('SettingsPage AI Governance Management', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(policiesApi, 'fetchPolicies').mockResolvedValue(mockPolicies);
    vi.spyOn(policiesApi, 'fetchPolicySummary').mockResolvedValue(mockSummary);
    vi.spyOn(policiesApi, 'fetchPolicyAuditLogs').mockResolvedValue([]);
  });

  it('renders settings title, summary metrics, and policy table', async () => {
    renderSettingsPage();

    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText(/Enterprise AI Provider Governance Policies/i)).toBeInTheDocument();
    expect(screen.getByText(/Backend Ingestion Binding/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
      expect(screen.getByText('POL-OPENAI-001')).toBeInTheDocument();
      expect(screen.getByText('POL-ANTHROPIC-002')).toBeInTheDocument();
    });
  });

  it('filters policies by search query', async () => {
    renderSettingsPage();

    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search policies by provider/i);
    fireEvent.change(searchInput, { target: { value: 'Anthropic' } });

    expect(screen.getByText('Anthropic')).toBeInTheDocument();
    expect(screen.queryByText('POL-OPENAI-001')).not.toBeInTheDocument();
  });

  it('filters policies by status tab', async () => {
    renderSettingsPage();

    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
    });

    const approvedTab = screen.getByRole('button', { name: /^APPROVED$/i });
    fireEvent.click(approvedTab);

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.queryByText('Anthropic')).not.toBeInTheDocument();
  });

  it('opens register policy modal when clicking REGISTER POLICY', async () => {
    renderSettingsPage();

    const registerBtn = screen.getByRole('button', { name: /REGISTER POLICY/i });
    fireEvent.click(registerBtn);

    expect(screen.getByText('Register AI Provider Policy')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e\.g\. OpenAI, Anthropic/i)).toBeInTheDocument();
  });

  it('opens confirmation modal when clicking BLOCK or APPROVE', async () => {
    renderSettingsPage();

    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
    });

    // OpenAI is approved, so its action button is BLOCK
    const blockBtn = screen.getByRole('button', { name: /^BLOCK$/i });
    fireEvent.click(blockBtn);

    expect(screen.getByText(/Revoke Approval: OpenAI/i)).toBeInTheDocument();
    expect(screen.getByText(/Are you sure you want to block and classify "OpenAI"/i)).toBeInTheDocument();
  });

  it('opens audit trail drawer when clicking VIEW AUDIT TRAIL', async () => {
    renderSettingsPage();

    const auditBtn = screen.getByRole('button', { name: /VIEW AUDIT TRAIL/i });
    fireEvent.click(auditBtn);

    expect(screen.getByText('Policy Governance Audit Trail')).toBeInTheDocument();
  });
});
