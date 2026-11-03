"use client";

import React, { useSyncExternalStore } from "react";

interface ClientOnlyProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

const emptySubscribe = () => () => {};

/**
 * Ensures child components are rendered strictly on the client after hydration,
 * preventing server/client DOM mismatch during initial hydration using React's
 * official useSyncExternalStore API.
 */
export function ClientOnly({ children, fallback = null }: ClientOnlyProps) {
  const isClient = useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );

  if (!isClient) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

export default ClientOnly;
