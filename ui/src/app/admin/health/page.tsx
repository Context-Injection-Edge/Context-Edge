'use client';

import { useEffect, useState } from 'react';

// ============================================================================
// TYPES
// ============================================================================

interface AdapterHealth {
  config_id: number;
  name: string;
  protocol: string;
  host: string;
  port: number;
  enabled: boolean;
  status: 'healthy' | 'degraded' | 'failed' | 'unknown';
  is_connected: boolean;
  response_time_ms: number;
  success_rate: number;
  error_count: number;
  last_error: string;
  last_error_at: string;
  checked_at: string;
}

// ============================================================================
// COMPONENTS
// ============================================================================

function TrafficLight({ status, size = 'md' }: { status: 'healthy' | 'degraded' | 'failed' | 'unknown', size?: 'sm' | 'md' | 'lg' }) {
  const sizes = {
    sm: 'w-3 h-3',
    md: 'w-6 h-6',
    lg: 'w-12 h-12'
  };

  const colors = {
    healthy: 'bg-green-500 shadow-green-500/50',
    degraded: 'bg-yellow-500 shadow-yellow-500/50',
    failed: 'bg-red-500 shadow-red-500/50',
    unknown: 'bg-gray-400 shadow-gray-400/50'
  };

  return (
    <div className="relative">
      {/* Glow effect */}
      <div className={`absolute inset-0 ${sizes[size]} rounded-full ${colors[status]} animate-pulse opacity-30 blur-md`} />
      {/* Main light */}
      <div className={`relative ${sizes[size]} rounded-full ${colors[status]} shadow-lg`} />
    </div>
  );
}

function HealthMeter({ percentage, label }: { percentage: number, label: string }) {
  let color = 'bg-green-500';
  let textColor = 'text-green-700';
  let bgColor = 'bg-green-100';

  if (percentage < 50) {
    color = 'bg-red-500';
    textColor = 'text-red-700';
    bgColor = 'bg-red-100';
  } else if (percentage < 80) {
    color = 'bg-yellow-500';
    textColor = 'text-yellow-700';
    bgColor = 'bg-yellow-100';
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className={`text-sm font-bold ${textColor}`}>{percentage.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full ${color} transition-all duration-500 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function ResponseTimeChart({ responseTime }: { responseTime: number }) {
  let status: 'healthy' | 'degraded' | 'failed' = 'healthy';
  let message = 'Excellent';

  if (responseTime > 500) {
    status = 'failed';
    message = 'Slow';
  } else if (responseTime > 200) {
    status = 'degraded';
    message = 'Warning';
  }

  const bars = [
    { threshold: 100, label: '< 100ms', active: responseTime < 100 },
    { threshold: 200, label: '< 200ms', active: responseTime < 200 },
    { threshold: 500, label: '< 500ms', active: responseTime < 500 },
    { threshold: 1000, label: '< 1s', active: responseTime < 1000 },
  ];

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <TrafficLight status={status} size="sm" />
        <span className="text-sm font-medium">{responseTime}ms - {message}</span>
      </div>
      <div className="flex gap-2">
        {bars.map((bar, idx) => (
          <div key={idx} className="flex-1">
            <div
              className={`h-8 rounded transition-all ${
                bar.active
                  ? 'bg-green-500'
                  : responseTime < bar.threshold + 100
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
            />
            <div className="text-xs text-center text-gray-600 mt-1">{bar.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function HealthDashboard() {
  const [healthData, setHealthData] = useState<AdapterHealth[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchHealth = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/devices/health');
      if (response.ok) {
        const data = await response.json();
        setHealthData(data);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch health:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();

    // Auto-refresh every 3 seconds
    const interval = setInterval(fetchHealth, 3000);
    return () => clearInterval(interval);
  }, []);

  // Calculate overall stats
  const stats = {
    total: healthData.filter(d => d.enabled).length,
    healthy: healthData.filter(d => d.enabled && d.status === 'healthy').length,
    degraded: healthData.filter(d => d.enabled && d.status === 'degraded').length,
    failed: healthData.filter(d => d.enabled && d.status === 'failed').length,
    avgResponseTime: healthData.length > 0
      ? healthData.reduce((sum, d) => sum + (d.response_time_ms || 0), 0) / healthData.filter(d => d.response_time_ms).length
      : 0,
    avgSuccessRate: healthData.length > 0
      ? healthData.reduce((sum, d) => sum + (d.success_rate || 0), 0) / healthData.filter(d => d.success_rate !== null).length
      : 0
  };

  const overallHealth = stats.total === 0 ? 0 : (stats.healthy / stats.total) * 100;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              System Health Monitor
            </h1>
            <p className="text-gray-600">
              Real-time connection status and performance metrics
            </p>
          </div>

          <div className="text-right">
            <div className="text-sm text-gray-500">Last updated</div>
            <div className="text-lg font-mono font-bold text-gray-900">
              {lastUpdate.toLocaleTimeString()}
            </div>
            <div className="flex items-center gap-2 justify-end mt-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-green-600">Live</span>
            </div>
          </div>
        </div>

        {/* Overall Health Card */}
        <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl shadow-2xl p-8 mb-8 text-white">
          <div className="grid grid-cols-2 gap-8">
            {/* Left side - Traffic light */}
            <div className="flex items-center gap-6">
              <div className="relative">
                {/* Traffic light box */}
                <div className="bg-gray-900 rounded-2xl p-6 shadow-2xl">
                  <div className="space-y-4">
                    <div className={`transition-opacity ${stats.failed > 0 ? 'opacity-100' : 'opacity-30'}`}>
                      <TrafficLight status="failed" size="lg" />
                    </div>
                    <div className={`transition-opacity ${stats.degraded > 0 ? 'opacity-100' : 'opacity-30'}`}>
                      <TrafficLight status="degraded" size="lg" />
                    </div>
                    <div className={`transition-opacity ${stats.healthy > 0 ? 'opacity-100' : 'opacity-30'}`}>
                      <TrafficLight status="healthy" size="lg" />
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <div className="text-6xl font-bold mb-2">
                  {overallHealth.toFixed(0)}%
                </div>
                <div className="text-xl opacity-90">
                  Overall System Health
                </div>
                <div className="text-sm opacity-75 mt-2">
                  {stats.healthy} of {stats.total} devices healthy
                </div>
              </div>
            </div>

            {/* Right side - Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/10 backdrop-blur rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrafficLight status="healthy" size="sm" />
                  <span className="text-sm opacity-75">Healthy</span>
                </div>
                <div className="text-4xl font-bold">{stats.healthy}</div>
              </div>

              <div className="bg-white/10 backdrop-blur rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrafficLight status="degraded" size="sm" />
                  <span className="text-sm opacity-75">Degraded</span>
                </div>
                <div className="text-4xl font-bold">{stats.degraded}</div>
              </div>

              <div className="bg-white/10 backdrop-blur rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrafficLight status="failed" size="sm" />
                  <span className="text-sm opacity-75">Failed</span>
                </div>
                <div className="text-4xl font-bold">{stats.failed}</div>
              </div>

              <div className="bg-white/10 backdrop-blur rounded-lg p-4">
                <div className="text-sm opacity-75 mb-2">Avg Response</div>
                <div className="text-4xl font-bold">
                  {stats.avgResponseTime.toFixed(0)}
                  <span className="text-xl ml-1">ms</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold mb-4">Average Success Rate</h3>
            <HealthMeter percentage={stats.avgSuccessRate} label="Connection Success Rate" />
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold mb-4">System Uptime</h3>
            <HealthMeter percentage={overallHealth} label="Devices Online" />
          </div>
        </div>

        {/* Individual Device Health */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-6">Device Health Details</h2>

          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-gray-600">Loading health data...</p>
            </div>
          ) : healthData.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📊</div>
              <p className="text-gray-600">No devices to monitor</p>
            </div>
          ) : (
            <div className="space-y-4">
              {healthData.map((device) => (
                <div
                  key={device.config_id}
                  className={`rounded-lg p-6 transition-all ${
                    !device.enabled
                      ? 'bg-gray-50 border border-gray-200'
                      : device.status === 'healthy'
                      ? 'bg-green-50 border-2 border-green-300'
                      : device.status === 'degraded'
                      ? 'bg-yellow-50 border-2 border-yellow-300'
                      : device.status === 'failed'
                      ? 'bg-red-50 border-2 border-red-300'
                      : 'bg-gray-50 border border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <TrafficLight status={device.enabled ? device.status : 'unknown'} size="md" />
                      <div>
                        <h3 className="text-xl font-bold text-gray-900">{device.name}</h3>
                        <p className="text-sm text-gray-600">
                          {device.host}:{device.port} • {device.protocol.toUpperCase()}
                        </p>
                      </div>
                    </div>

                    <div className={`px-4 py-2 rounded-full font-bold ${
                      device.enabled
                        ? device.is_connected
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {device.enabled
                        ? device.is_connected ? 'CONNECTED' : 'DISCONNECTED'
                        : 'DISABLED'
                      }
                    </div>
                  </div>

                  {device.enabled && (
                    <div className="grid grid-cols-3 gap-6">
                      {/* Response Time */}
                      <div>
                        <ResponseTimeChart responseTime={device.response_time_ms || 0} />
                      </div>

                      {/* Success Rate */}
                      <div>
                        <HealthMeter
                          percentage={(device.success_rate || 0) * 100}
                          label="Success Rate"
                        />
                      </div>

                      {/* Error Count */}
                      <div>
                        <div className="text-sm font-medium text-gray-700 mb-2">Error Count</div>
                        <div className={`text-4xl font-bold ${
                          device.error_count === 0
                            ? 'text-green-600'
                            : device.error_count < 5
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}>
                          {device.error_count || 0}
                        </div>
                        {device.last_error && (
                          <div className="mt-2 text-xs text-red-600 truncate">
                            {device.last_error}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
