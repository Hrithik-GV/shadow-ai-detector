import { Component, type ErrorInfo, type ReactNode } from 'react';
import { ShieldAlert, RotateCcw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Unhandled React Error in ErrorBoundary:', error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-6 bg-[#0D0D0D] font-mono text-xs">
          <div className="max-w-md w-full bg-[#171716] border-2 border-[#732626] shadow-[6px_6px_0_#000000] p-6 space-y-4 text-center">
            <div className="w-12 h-12 mx-auto bg-[#2A1616] border-2 border-[#8C2323] shadow-[2px_2px_0_#000000] flex items-center justify-center text-[#FF6B6B]">
              <ShieldAlert className="w-6 h-6" />
            </div>

            <div>
              <h2 className="text-sm font-bold text-[#FF6B6B] uppercase tracking-wide">
                {this.props.fallbackTitle || 'Application Render Error'}
              </h2>
              <p className="text-[#9A9A91] text-[11px] mt-1 leading-relaxed">
                An unexpected interface rendering issue was caught by the security console boundary.
              </p>
            </div>

            {this.state.error && (
              <div className="p-2.5 bg-[#0D0D0D] border border-[#333330] text-[#FF6B6B] text-[10px] text-left overflow-x-auto">
                {this.state.error.message}
              </div>
            )}

            <div className="pt-2">
              <Button
                variant="primary"
                size="sm"
                icon={<RotateCcw className="w-3.5 h-3.5" />}
                onClick={this.handleReload}
              >
                RELOAD CONSOLE
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
