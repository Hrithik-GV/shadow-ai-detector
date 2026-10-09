import { AlertTriangle, RefreshCw, ShieldX } from 'lucide-react';
import { Button } from './Button';
import { Badge } from './Badge';
import { API_BASE_URL } from '../../lib/config';

export interface QueryErrorStateProps {
  error: unknown;
  onRetry?: () => void;
  title?: string;
  isRetrying?: boolean;
  className?: string;
}

export const QueryErrorState: React.FC<QueryErrorStateProps> = ({
  error,
  onRetry,
  title = 'API Connection Error',
  isRetrying = false,
  className = '',
}) => {
  const errObj = typeof error === 'object' && error !== null ? (error as Record<string, unknown>) : {};
  const message =
    typeof errObj.message === 'string'
      ? errObj.message
      : 'Failed to communicate with the Shadow AI detection backend.';
  const status = typeof errObj.status === 'number' ? errObj.status : undefined;
  const code = typeof errObj.code === 'string' ? errObj.code : undefined;

  return (
    <div
      className={`border-2 border-[#732626] bg-[#171716] shadow-[4px_4px_0_#000000] p-6 sm:p-8 text-left ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-[#333330]">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-[#2A1616] border-2 border-[#8C2323] shadow-[2px_2px_0_#000000] flex items-center justify-center shrink-0">
            <ShieldX className="w-5 h-5 text-[#FF6B6B]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-mono text-sm sm:text-base font-bold text-[#FF6B6B] tracking-wide uppercase">
                {title}
              </h3>
              {status !== undefined && status > 0 && (
                <Badge variant="danger" size="sm">
                  HTTP {status}
                </Badge>
              )}
              {status === 0 && (
                <Badge variant="danger" size="sm">
                  OFFLINE
                </Badge>
              )}
            </div>
            <p className="font-mono text-xs text-[#9A9A91] mt-1">
              Backend endpoint:{' '}
              <span className="text-[#F4F4F0] font-semibold">{API_BASE_URL}</span>
            </p>
          </div>
        </div>

        {onRetry && (
          <Button
            variant="primary"
            size="sm"
            onClick={onRetry}
            disabled={isRetrying}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${isRetrying ? 'animate-spin' : ''}`} />}
          >
            {isRetrying ? 'RETRYING...' : 'RETRY REQUEST'}
          </Button>
        )}
      </div>

      <div className="mt-4 space-y-3 font-mono text-xs">
        <div className="p-3 bg-[#0D0D0D] border border-[#333330] text-[#FF6B6B] leading-relaxed">
          <span className="font-bold text-[#FFCC00] uppercase block text-[10px] mb-1">
            Error Details {code ? `[${code}]` : ''}
          </span>
          {message}
        </div>

        <div className="flex items-center gap-2 text-[11px] text-[#9A9A91]">
          <AlertTriangle className="w-3.5 h-3.5 text-[#FFCC00] shrink-0" />
          <span>
            No mock fallback data is used. Ensure backend service is reachable at the configured target.
          </span>
        </div>
      </div>
    </div>
  );
};
