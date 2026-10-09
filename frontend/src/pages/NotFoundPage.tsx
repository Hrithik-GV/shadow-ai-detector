import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/common/PageContainer';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageContainer title="404 - Not Found" description="The requested route does not exist.">
      <EmptyState
        title="Page Not Found"
        description="The navigation route you accessed is not recognized by the security console."
        statusLabel="ERROR 404"
        icon={<ShieldAlert className="w-7 h-7 text-[#FF6B6B]" />}
        action={
          <Button
            variant="primary"
            size="md"
            icon={<ArrowLeft className="w-3.5 h-3.5" />}
            onClick={() => navigate('/')}
          >
            RETURN TO OVERVIEW
          </Button>
        }
      />
    </PageContainer>
  );
};
