'use client';

import { useState, useEffect } from 'react';

interface AIModel {
  version_id: string;
  name?: string;
  description?: string;
  accuracy: number;
  created_at: string;
  status: 'ready_for_review' | 'deploying_pilot' | 'pilot_success' | 'deploying_all' | 'deployed' | 'rolled_back';
  deployed_devices?: string[];
  pilot_devices?: string[];
  training_samples?: number;
  model_path?: string;
}

interface EdgeDevice {
  device_id: string;
  name: string;
  current_model: string;
  status: 'online' | 'offline';
  last_seen?: string;
}

interface PilotMetrics {
  version_id: string;
  pilot_devices: number;
  online_devices: number;
  total_predictions: number;
  accuracy: number;
  false_positive_rate: number;
  false_negative_rate: number;
  errors: number;
  avg_inference_time_ms: number;
  monitoring_duration_hours: number;
}

export default function ModelsPage() {
  const [pendingModels, setPendingModels] = useState<AIModel[]>([]);
  const [deployedModels, setDeployedModels] = useState<AIModel[]>([]);
  const [devices, setDevices] = useState<EdgeDevice[]>([]);
  const [pilotMetrics, setPilotMetrics] = useState<PilotMetrics | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [deploying, setDeploying] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [monitoringVersion, setMonitoringVersion] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchPendingModels();
    fetchDeployedModels();
    fetchDevices();
  }, []);

  // Poll pilot metrics every minute if monitoring
  useEffect(() => {
    if (!monitoringVersion) return;

    const interval = setInterval(() => {
      fetchPilotMetrics(monitoringVersion);
    }, 60000); // Poll every 60 seconds

    fetchPilotMetrics(monitoringVersion); // Fetch immediately

    return () => clearInterval(interval);
  }, [monitoringVersion]);

  const fetchPendingModels = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/mlops/models/pending`);
      const data = await response.json();
      setPendingModels(data.models || []);
    } catch (error) {
      console.error('Error fetching pending models:', error);
      // Fallback to mock data for development
      setPendingModels([
        {
          version_id: 'v2.2',
          accuracy: 0.95,
          created_at: '2025-01-15T08:00:00Z',
          status: 'ready_for_review',
          training_samples: 100000,
          model_path: 's3://models/model-v2.2.trt'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchDeployedModels = async () => {
    try {
      // In production, this would be a separate endpoint
      // For now, use mock data for deployed models
      const mockDeployed: AIModel[] = [
        {
          version_id: 'v2.1',
          accuracy: 0.94,
          created_at: '2025-01-10T08:00:00Z',
          status: 'deployed',
          deployed_devices: ['edge-001', 'edge-002', 'edge-003', 'edge-004', 'edge-005']
        },
        {
          version_id: 'v2.0',
          accuracy: 0.89,
          created_at: '2025-01-05T10:00:00Z',
          status: 'deployed',
          deployed_devices: []
        }
      ];
      setDeployedModels(mockDeployed);
    } catch (error) {
      console.error('Error fetching deployed models:', error);
    }
  };

  const fetchDevices = async () => {
    try {
      const response = await fetch(`${API_BASE}/mlops/devices/status`);
      const data = await response.json();
      setDevices(data.devices || []);
    } catch (error) {
      console.error('Error fetching devices:', error);
      // Use mock devices as fallback
      const mockDevices = [
        {
          device_id: 'edge-001',
          name: 'CIM-Line1-Station1',
          current_model: 'v1.5',
          status: 'online',
          last_seen: '2025-01-15T14:30:00Z'
        },
        {
          device_id: 'edge-002',
          name: 'CIM-Line1-Station2',
          current_model: 'v1.5',
          status: 'online',
          last_seen: '2025-01-15T14:25:00Z'
        },
        {
          device_id: 'edge-003',
          name: 'CIM-Line2-Station1',
          current_model: 'v1.4',
          status: 'online',
          last_seen: '2025-01-15T14:20:00Z'
        },
        {
          device_id: 'edge-004',
          name: 'CIM-Quality-Control',
          current_model: 'v1.5',
          status: 'offline',
          last_seen: '2025-01-15T10:00:00Z'
        }
      ];
      setDevices(mockDevices);
    }
  };

  const deployModel = async (modelVersion: string, deviceIds: string[]) => {
    setDeploying(modelVersion);
    try {
      // In real implementation, this would trigger Kubernetes deployment
      alert(`Deploying ${modelVersion} to ${deviceIds.length} device(s)...`);

      // Simulate deployment delay
      setTimeout(() => {
        // Update model status
        setModels(models.map(model =>
          model.version_id === modelVersion
            ? { ...model, status: 'deployed' as const, deployed_devices: [...new Set([...model.deployed_devices, ...deviceIds])] }
            : model
        ));

        // Update device current model
        setDevices(devices.map(device =>
          deviceIds.includes(device.device_id)
            ? { ...device, current_model: modelVersion }
            : device
        ));

        setDeploying(null);
        alert('Deployment completed successfully');
      }, 2000);

    } catch (error) {
      console.error('Error deploying model:', error);
      setDeploying(null);
      alert('Deployment failed');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-600';
      case 'offline': return 'text-red-600';
      case 'deployed': return 'text-blue-600';
      case 'available': return 'text-gray-900';
      case 'deploying': return 'text-yellow-600';
      default: return 'text-gray-900';
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      online: 'bg-green-100 text-green-800',
      offline: 'bg-red-100 text-red-800',
      deployed: 'bg-blue-100 text-blue-800',
      available: 'bg-gray-100 text-gray-800',
      deploying: 'bg-yellow-100 text-yellow-800'
    };
    return colors[status as keyof typeof colors] || colors.available;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">MLOps Dashboard</h1>
          <a
            href="/admin"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Admin
          </a>
        </div>

        {loading ? (
          <div className="text-center py-8">Loading models...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Model Repository */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">AI Model Repository</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {models.map((model) => (
                  <div key={model.version_id} className="p-6">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-gray-900">{model.name}</h3>
                        <p className="text-sm text-gray-900">Version: {model.version_id}</p>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(model.status)}`}>
                        {model.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-3">{model.description}</p>
                    <div className="flex justify-between items-center text-sm text-gray-900 mb-3">
                      <span>Accuracy: {(model.accuracy * 100).toFixed(1)}%</span>
                      <span>Created: {new Date(model.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-900">
                        Deployed to {model.deployed_devices.length} device(s)
                      </span>
                      <button
                        onClick={() => deployModel(model.version_id, devices.filter(d => d.status === 'online').map(d => d.device_id))}
                        disabled={deploying === model.version_id || devices.filter(d => d.status === 'online').length === 0}
                        className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                        title="Deploy this trained model to all online edge devices"
                      >
                        {deploying === model.version_id ? 'Deploying...' : 'Deploy Model to All Devices'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Edge Device Status */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Edge Device Status</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {devices.map((device) => (
                  <div key={device.device_id} className="p-6">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-gray-900">{device.name}</h3>
                        <p className="text-sm text-gray-900">ID: {device.device_id}</p>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(device.status)}`}>
                        {device.status}
                      </span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-900">Current Model:</span>
                        <span className="font-mono">{device.current_model}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-900">Last Seen:</span>
                        <span className={getStatusColor(device.status)}>
                          {new Date(device.last_seen).toLocaleString()}
                        </span>
                      </div>
                    </div>
                    {device.status === 'online' && (
                      <div className="mt-3 flex gap-2">
                        <select
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                        >
                          <option value="">Select model to deploy</option>
                          {models.map(model => (
                            <option key={model.version_id} value={model.version_id}>
                              {model.version_id} - {model.name}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={() => selectedModel && deployModel(selectedModel, [device.device_id])}
                          disabled={!selectedModel || deploying === selectedModel}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          Deploy
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Model Performance Summary */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Model Performance Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {models.filter(m => m.status === 'deployed').length}
              </div>
              <div className="text-gray-900">Active Models</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {devices.filter(d => d.status === 'online').length}/{devices.length}
              </div>
              <div className="text-gray-900">Online Devices</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {(models.reduce((acc, m) => acc + m.accuracy, 0) / models.length * 100).toFixed(1)}%
              </div>
              <div className="text-gray-900">Average Accuracy</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}