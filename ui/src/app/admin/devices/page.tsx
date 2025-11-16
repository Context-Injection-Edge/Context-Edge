
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

// ============================================================================
// TYPES
// ============================================================================

interface DeviceConfig {
  config_id: number;
  name: string;
  protocol: string;
  host: string;
  port: number;
  enabled: boolean;
  template_id: string;
  vendor: string;
  model: string;
  health_status: 'healthy' | 'degraded' | 'failed' | 'unknown';
  is_connected: boolean;
  response_time_ms: number;
  last_error: string;
  last_connected_at: string;
  updated_at: string;
}

// ============================================================================
// STATUS COMPONENTS
// ============================================================================

function StatusLight({ status }: { status: 'healthy' | 'degraded' | 'failed' | 'unknown' | 'disabled' }) {
  const colors = {
    healthy: 'bg-green-500',
    degraded: 'bg-yellow-500',
    failed: 'bg-red-500',
    unknown: 'bg-gray-400',
    disabled: 'bg-gray-300'
  };

  const pulseColors = {
    healthy: 'animate-pulse bg-green-400',
    degraded: 'animate-pulse bg-yellow-400',
    failed: 'animate-pulse bg-red-400',
    unknown: '',
    disabled: ''
  };

  return (
    <div className="relative w-4 h-4">
      {/* Outer glow */}
      {status !== 'unknown' && status !== 'disabled' && (
        <div className={`absolute inset-0 rounded-full ${pulseColors[status]} opacity-50`} />
      )}
      {/* Main light */}
      <div className={`absolute inset-0 rounded-full ${colors[status]} shadow-lg`} />
    </div>
  );
}

function StatusBadge({ status, enabled }: { status: 'healthy' | 'degraded' | 'failed' | 'unknown', enabled: boolean }) {
  if (!enabled) {
    return (
      <div className="flex items-center gap-2 px-3 py-1 bg-gray-700 border border-gray-600 rounded-full">
        <StatusLight status="disabled" />
        <span className="text-sm font-medium text-gray-300">Disabled</span>
      </div>
    );
  }

  const config = {
    healthy: {
      bg: 'bg-green-900',
      border: 'border-green-700',
      text: 'text-green-200',
      label: 'Connected'
    },
    degraded: {
      bg: 'bg-yellow-900',
      border: 'border-yellow-700',
      text: 'text-yellow-200',
      label: 'Degraded'
    },
    failed: {
      bg: 'bg-red-900',
      border: 'border-red-700',
      text: 'text-red-200',
      label: 'Failed'
    },
    unknown: {
      bg: 'bg-gray-800',
      border: 'border-gray-700',
      text: 'text-gray-400',
      label: 'Unknown'
    }
  };

  const c = config[status];

  return (
    <div className={`flex items-center gap-2 px-3 py-1 ${c.bg} border ${c.border} rounded-full`}>
      <StatusLight status={status} />
      <span className={`text-sm font-medium ${c.text}`}>{c.label}</span>
    </div>
  );
}

function ResponseTimeBadge({ ms }: { ms: number | null }) {
  if (ms === null || ms === undefined) {
    return null;
  }

  let color = 'bg-green-800 text-green-200';
  let icon = '🟢';

  if (ms > 500) {
    color = 'bg-red-800 text-red-200';
    icon = '🔴';
  } else if (ms > 200) {
    color = 'bg-yellow-800 text-yellow-200';
    icon = '🟡';
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${color}`}>
      {icon} {ms}ms
    </span>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DevicesPage() {
  const [devices, setDevices] = useState<DeviceConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [serverConnected, setServerConnected] = useState(true); // Assume connected, AdminNav shows status
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch devices
  const fetchDevices = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/devices/configs');
      if (response.ok) {
        const data = await response.json();
        setDevices(data);
        setServerConnected(true);
      } else {
        setServerConnected(false);
      }
    } catch (error) {
      console.error('Failed to fetch devices:', error);
      setServerConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchDevices();
  }, []);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchDevices();
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Enable/Disable device
  const toggleDevice = async (configId: number, currentEnabled: boolean) => {
    try {
      const action = currentEnabled ? 'disable' : 'enable';
      const response = await fetch(
        `http://localhost:5000/api/admin/devices/configs/${configId}/${action}`,
        { method: 'POST' }
      );

      if (response.ok) {
        fetchDevices();
      } else {
        alert('Failed to toggle device');
      }
    } catch (error) {
      console.error('Toggle error:', error);
      alert('Failed to toggle device');
    }
  };

  // Delete device
  const deleteDevice = async (configId: number, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:5000/api/admin/devices/configs/${configId}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        fetchDevices();
      } else {
        alert('Failed to delete device');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete device');
    }
  };

  // Count by status
  const stats = {
    total: devices.length,
    healthy: devices.filter(d => d.enabled && d.health_status === 'healthy').length,
    degraded: devices.filter(d => d.enabled && d.health_status === 'degraded').length,
    failed: devices.filter(d => d.enabled && d.health_status === 'failed').length,
    disabled: devices.filter(d => !d.enabled).length
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">
            Device Management
          </h1>
          <p className="text-gray-400">
            Manage connections to PLCs, MES, ERP, and other industrial systems
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg font-medium ${
              autoRefresh
                ? 'bg-blue-800 text-blue-200 border border-blue-600'
                : 'bg-gray-700 text-gray-300 border border-gray-600'
            }`}
          >
            {autoRefresh ? '🔄 Auto-refresh ON' : '⏸️ Auto-refresh OFF'}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        <div className="bg-gray-800 rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div className="text-3xl font-bold text-white">{stats.total}</div>
          <div className="text-sm text-gray-400 mt-1">Total Devices</div>
        </div>

        <div className="bg-gray-800 rounded-lg shadow p-6 border-l-4 border-green-500">
          <div className="flex items-center gap-2">
            <StatusLight status="healthy" />
            <div className="text-3xl font-bold text-green-400">{stats.healthy}</div>
          </div>
          <div className="text-sm text-gray-400 mt-1">🟢 Healthy</div>
        </div>

        <div className="bg-gray-800 rounded-lg shadow p-6 border-l-4 border-yellow-500">
          <div className="flex items-center gap-2">
            <StatusLight status="degraded" />
            <div className="text-3xl font-bold text-yellow-400">{stats.degraded}</div>
          </div>
          <div className="text-sm text-gray-400 mt-1">🟡 Degraded</div>
        </div>

        <div className="bg-gray-800 rounded-lg shadow p-6 border-l-4 border-red-500">
          <div className="flex items-center gap-2">
            <StatusLight status="failed" />
            <div className="text-3xl font-bold text-red-400">{stats.failed}</div>
          </div>
          <div className="text-sm text-gray-400 mt-1">🔴 Failed</div>
        </div>

        <div className="bg-gray-800 rounded-lg shadow p-6 border-l-4 border-gray-500">
          <div className="flex items-center gap-2">
            <StatusLight status="disabled" />
            <div className="text-3xl font-bold text-gray-400">{stats.disabled}</div>
          </div>
          <div className="text-sm text-gray-400 mt-1">⚪ Disabled</div>
        </div>
      </div>

      {/* Devices List */}
      {!serverConnected ? (
        <div className="bg-gray-800 rounded-lg shadow-lg p-12 text-center">
          <div className="text-6xl mb-4">🔌</div>
          <h2 className="text-3xl font-bold text-white mb-2">
            Edge Server is Offline
          </h2>
          <p className="text-gray-400 mb-6">
            The UI cannot connect to the Edge Server. Please ensure it is running.
          </p>
          <button
            onClick={fetchDevices}
            className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700"
          >
            Retry Connection
          </button>
        </div>
      ) : isLoading ? (
        <div className="bg-gray-800 rounded-lg shadow p-12 text-center">
          <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-400">Loading devices...</p>
        </div>
      ) : devices.length === 0 ? (
        <div className="bg-gray-800 rounded-lg shadow-lg p-12 text-center">
          <div className="text-6xl mb-4">🏭</div>
          <h2 className="text-3xl font-bold text-white mb-2">
            No Devices Configured
          </h2>
          <p className="text-gray-400 mb-6">
            Get started by adding your first industrial device using the wizard.
          </p>
          <Link
            href="/admin/devices/setup-wizard"
            className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700"
          >
            + Add Your First Device
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {devices.map((device) => (
            <div
              key={device.config_id}
              className="bg-gray-800 rounded-lg shadow-lg hover:shadow-blue-500/20 transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  {/* Left side - Device info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-3">
                      {/* Protocol icon */}
                      <div className="text-4xl">
                        {device.protocol === 'modbus_tcp' && '🔌'}
                        {device.protocol === 'opcua' && '🌐'}
                        {device.protocol === 'ethernet_ip' && '🔗'}
                        {device.protocol === 'http' && '☁️'}
                      </div>

                      <div className="flex-1">
                        <h3 className="text-2xl font-bold text-white mb-1">
                          {device.name}
                        </h3>
                        <div className="flex items-center gap-3 text-sm text-gray-400">
                          <span className="font-medium">
                            {device.vendor} {device.model}
                          </span>
                          <span>•</span>
                          <span>{device.host}:{device.port}</span>
                          <span>•</span>
                          <span className="uppercase font-mono text-xs bg-gray-700 px-2 py-1 rounded">
                            {device.protocol.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Status row */}
                    <div className="flex items-center gap-4 mt-4">
                      <StatusBadge
                        status={device.health_status || 'unknown'}
                        enabled={device.enabled}
                      />

                      {device.enabled && (
                        <>
                          <ResponseTimeBadge ms={device.response_time_ms} />

                          {device.last_error && (
                            <div className="flex items-center gap-2 text-sm text-red-400">
                              <span>⚠️</span>
                              <span className="truncate max-w-md">{device.last_error}</span>
                            </div>
                          )}

                          {device.last_connected_at && (
                            <span className="text-sm text-gray-500">
                              Last connected: {new Date(device.last_connected_at).toLocaleString()}
                            </span>
                          )}
                        </>
                      )}
                    </div>
                  </div>

                  {/* Right side - Actions */}
                  <div className="flex flex-col gap-2 ml-6">
                    <button
                      onClick={() => toggleDevice(device.config_id, device.enabled)}
                      className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                        device.enabled
                          ? 'bg-yellow-800 text-yellow-200 hover:bg-yellow-700 border border-yellow-600'
                          : 'bg-green-800 text-green-200 hover:bg-green-700 border border-green-600'
                      }`}
                    >
                      {device.enabled ? '⏸️ Disable' : '▶️ Enable'}
                    </button>

                    <button
                      onClick={() => {/* TODO: Edit modal */}}
                      className="px-4 py-2 bg-blue-800 text-blue-200 rounded-lg font-medium hover:bg-blue-700 border border-blue-600"
                    >
                      ✏️ Edit
                    </button>

                    <button
                      onClick={() => deleteDevice(device.config_id, device.name)}
                      className="px-4 py-2 bg-red-800 text-red-200 rounded-lg font-medium hover:bg-red-700 border border-red-600"
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              </div>

              {/* Connection health details (expandable section) */}
              {device.enabled && device.health_status === 'failed' && (
                <div className="border-t border-red-700 bg-red-900/50 px-6 py-4">
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">🔴</div>
                    <div className="flex-1">
                      <h4 className="font-bold text-red-200 mb-1">Connection Failed</h4>
                      <p className="text-sm text-red-300">
                        {device.last_error || 'Unable to establish connection'}
                      </p>
                      <div className="mt-2 flex gap-2">
                        <button className="text-sm text-red-200 hover:text-red-100 font-medium underline">
                          View Logs
                        </button>
                        <button className="text-sm text-red-200 hover:text-red-100 font-medium underline">
                          Test Connection
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {device.enabled && device.health_status === 'degraded' && (
                <div className="border-t border-yellow-700 bg-yellow-900/50 px-6 py-4">
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">🟡</div>
                    <div className="flex-1">
                      <h4 className="font-bold text-yellow-200 mb-1">Connection Degraded</h4>
                      <p className="text-sm text-yellow-300">
                        Slow response times or intermittent connectivity detected
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {device.enabled && device.health_status === 'healthy' && (
                <div className="border-t border-green-700 bg-green-900/50 px-6 py-4">
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">🟢</div>
                    <div className="flex-1">
                      <h4 className="font-bold text-green-200 mb-1">Connection Healthy</h4>
                      <p className="text-sm text-green-300">
                        All systems operational • Response time: {device.response_time_ms}ms
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
