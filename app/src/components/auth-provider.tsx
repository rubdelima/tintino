
'use client';

import { useAuth, AuthProviderWrapper } from '@/hooks/use-auth.tsx';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, ReactNode } from 'react';
import { Skeleton } from './ui/skeleton';

const publicRoutes = ['/', '/login', '/register'];

function AuthChecker({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading) {
      if (user && publicRoutes.includes(pathname)) {
        router.push('/home');
      }
      if (!user && !publicRoutes.includes(pathname)) {
        router.push('/login');
      }
    }
  }, [user, loading, router, pathname]);

  if (loading || (!user && !publicRoutes.includes(pathname)) || (user && publicRoutes.includes(pathname))) {
    return (
      <div className="flex min-h-screen w-full items-center justify-center">
        <div className="flex flex-col items-center gap-4">
            <Skeleton className="h-24 w-24 rounded-full" />
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-6 w-48" />
        </div>
      </div>
    );
  }
  
  return <>{children}</>;
}

export function AuthProvider({ children }: { children: ReactNode }) {
    return (
        <AuthProviderWrapper>
            <AuthChecker>{children}</AuthChecker>
        </AuthProviderWrapper>
    )
}
