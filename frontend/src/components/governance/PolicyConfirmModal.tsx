import React, { useState } from 'react';
import { Button } from '../common/Button';
import { X, AlertTriangle, Loader2 } from 'lucide-react';

export interface PolicyConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  confirmVariant?: 'primary' | 'danger' | 'secondary';
  isPending?: boolean;
  error?: string | null;
  showNotesField?: boolean;
  onConfirm: (notes?: string) => void;
  onClose: () => void;
}

export const PolicyConfirmModal: React.FC<PolicyConfirmModalProps> = ({
  isOpen,
  title,
  message,
  confirmText = 'CONFIRM',
  confirmVariant = 'danger',
  isPending = false,
  error = null,
  showNotesField = true,
  onConfirm,
  onClose,
}) => {
  const [notes, setNotes] = useState('');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-[#000000]/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-md border-2 border-[#333330] bg-[#121212] shadow-[8px_8px_0_#000000] font-mono text-xs">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b-2 border-[#333330] bg-[#181818]">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#FFCC00]" />
            <h3 className="font-bold text-[#F4F4F0] uppercase tracking-wider">{title}</h3>
          </div>
          <button
            onClick={onClose}
            disabled={isPending}
            className="text-[#9A9A91] hover:text-[#F4F4F0] p-1 border border-transparent hover:border-[#333330] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          <p className="text-[#F4F4F0] leading-relaxed">{message}</p>

          {error && (
            <div className="p-3 bg-[#FF4D4D]/10 border border-[#8C2323] text-[#FF6B6B]">
              {error}
            </div>
          )}

          {showNotesField && (
            <div className="space-y-1.5">
              <label className="text-[#9A9A91] text-[10px] uppercase tracking-wider block font-bold">
                Audit Reason / Admin Note (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Periodic security review compliance update"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                disabled={isPending}
                className="w-full bg-[#0D0D0D] border border-[#333330] px-3 py-2 text-[#F4F4F0] placeholder-[#666660] outline-none focus:border-[#FFCC00]"
              />
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#333330]">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={isPending}
            >
              CANCEL
            </Button>
            <Button
              type="button"
              variant={confirmVariant}
              size="sm"
              onClick={() => onConfirm(notes)}
              disabled={isPending}
              icon={isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : undefined}
            >
              {isPending ? 'PROCESSING...' : confirmText}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
