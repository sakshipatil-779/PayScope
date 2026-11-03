import { LandingClientContainer } from "@/components/landing/LandingClientContainer";
import { getApiBaseUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

interface HealthData {
  status: string;
  service: string;
  version: string;
}

interface HealthResult {
  connected: boolean;
  data: HealthData | null;
  error?: string;
  url: string;
  timestamp: string;
}

async function getBackendHealth(): Promise<HealthResult> {
  const baseUrl = getApiBaseUrl();
  const healthUrl = `${baseUrl.replace(/\/+$/, "")}/api/v1/health`;
  const timestamp = new Date().toISOString();

  try {
    const res = await fetch(healthUrl, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!res.ok) {
      return {
        connected: false,
        data: null,
        error: `HTTP ${res.status}: ${res.statusText}`,
        url: healthUrl,
        timestamp,
      };
    }

    const data: HealthData = await res.json();
    if (data.status === "ok") {
      return {
        connected: true,
        data,
        url: healthUrl,
        timestamp,
      };
    }

    return {
      connected: false,
      data,
      error: `Unexpected payload status: ${data.status}`,
      url: healthUrl,
      timestamp,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Connection failed";
    return {
      connected: false,
      data: null,
      error: message,
      url: healthUrl,
      timestamp,
    };
  }
}

export default async function Home() {
  const health = await getBackendHealth();

  return <LandingClientContainer apiConnected={health.connected} />;
}
