'use client';

import { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface MER {
  id: string;
  asset_id: string;
  timestamp: string;
  failure_mode: string;
  confidence: number;
  video_url?: string;
  sensor_data: {
    timestamps: string[];
    vibration: number[];
    temperature: number[];
    current: number[];
  };
  plc_snapshot: Record<string, any>;
}

export default function MERReportsPage() {
  const [mers, setMers] = useState<MER[]>([]);
  const [selectedMer, setSelectedMer] = useState<MER | null>(null);
  const [loading, setLoading] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchMers();
  }, []);

  const fetchMers = async () => {
    setLoading(true);
    try {
      // Mock data for now - in real implementation, this would call an API
      const mockMers: MER[] = [
        {
          id: 'mer-001',
          asset_id: 'Pump-A104',
          timestamp: '2025-01-15T10:30:00Z',
          failure_mode: 'Bearing Wear',
          confidence: 0.85,
          video_url: '/api/video/mer-001.mp4',
          sensor_data: {
            timestamps: Array.from({length: 65}, (_, i) => `T-${60-i}s`),
            vibration: Array.from({length: 65}, () => Math.random() * 2 + 0.5),
            temperature: Array.from({length: 65}, () => Math.random() * 20 + 60),
            current: Array.from({length: 65}, () => Math.random() * 5 + 8),
          },
          plc_snapshot: {
            operating_speed: '1200 RPM',
            load_percentage: '85%',
            cycle_count: '15420'
          }
        },
        {
          id: 'mer-002',
          asset_id: 'Motor-B205',
          timestamp: '2025-01-15T14:15:00Z',
          failure_mode: 'Belt Slippage',
          confidence: 0.92,
          sensor_data: {
            timestamps: Array.from({length: 65}, (_, i) => `T-${60-i}s`),
            vibration: Array.from({length: 65}, () => Math.random() * 1.5 + 0.3),
            temperature: Array.from({length: 65}, () => Math.random() * 15 + 55),
            current: Array.from({length: 65}, () => Math.random() * 3 + 7),
          },
          plc_snapshot: {
            operating_speed: '1800 RPM',
            load_percentage: '92%',
            cycle_count: '28950'
          }
        }
      ];
      setMers(mockMers);
    } catch (error) {
      console.error('Error fetching MERs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleValidation = async (merId: string, action: 'confirm' | 'false_alarm' | 'work_order') => {
    try {
      // In real implementation, call feedback API
      alert(`${action.replace('_', ' ').toUpperCase()} recorded for MER ${merId}`);
      // Remove from list or update status
      setMers(mers.filter(mer => mer.id !== merId));
      setSelectedMer(null);
    } catch (error) {
      console.error('Error submitting validation:', error);
    }
  };

  const chartData = selectedMer ? {
    labels: selectedMer.sensor_data.timestamps,
    datasets: [
      {
        label: 'Vibration (g)',
        data: selectedMer.sensor_data.vibration,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
        yAxisID: 'y',
      },
      {
        label: 'Temperature (°C)',
        data: selectedMer.sensor_data.temperature,
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
        yAxisID: 'y1',
      },
      {
        label: 'Current (A)',
        data: selectedMer.sensor_data.current,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        yAxisID: 'y1',
      },
    ],
  } : null;

  const chartOptions = {
    responsive: true,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    stacked: false,
    plugins: {
      title: {
        display: true,
        text: 'Sensor Timeline (60s before + 5s after event)',
      },
    },
    scales: {
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Vibration (g)',
        },
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Temperature (°C) / Current (A)',
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Maintenance Event Records (MER)</h1>
          <a
            href="/admin"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Admin
          </a>
        </div>

        {loading ? (
          <div className="text-center py-8">Loading MERs...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* MER List */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Active MERs</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {mers.map((mer) => (
                  <div
                    key={mer.id}
                    className={`p-4 cursor-pointer hover:bg-gray-50 ${
                      selectedMer?.id === mer.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                    onClick={() => setSelectedMer(mer)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{mer.asset_id}</h3>
                        <p className="text-sm text-gray-600">{mer.failure_mode}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(mer.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm font-semibold ${
                          mer.confidence > 0.8 ? 'text-green-600' :
                          mer.confidence > 0.6 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {(mer.confidence * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-500">confidence</div>
                      </div>
                    </div>
                  </div>
                ))}
                {mers.length === 0 && (
                  <div className="p-6 text-center text-gray-700">
                    No active MERs found.
                  </div>
                )}
              </div>
            </div>

            {/* MER Details */}
            <div className="bg-white rounded-lg shadow-md">
              {selectedMer ? (
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    MER Details: {selectedMer.id}
                  </h2>

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div>
                      <strong>Asset ID:</strong> {selectedMer.asset_id}
                    </div>
                    <div>
                      <strong>Failure Mode:</strong> {selectedMer.failure_mode}
                    </div>
                    <div>
                      <strong>Timestamp:</strong> {new Date(selectedMer.timestamp).toLocaleString()}
                    </div>
                    <div>
                      <strong>Confidence:</strong> {(selectedMer.confidence * 100).toFixed(1)}%
                    </div>
                  </div>

                  {/* Video Placeholder */}
                  {selectedMer.video_url && (
                    <div className="mb-6">
                      <h3 className="font-semibold mb-2">Video Evidence</h3>
                      <div className="bg-gray-200 h-32 flex items-center justify-center rounded">
                        <span className="text-gray-600">Video Player: {selectedMer.video_url}</span>
                      </div>
                    </div>
                  )}

                  {/* Sensor Chart */}
                  <div className="mb-6">
                    <h3 className="font-semibold mb-2">Sensor Timeline</h3>
                    {chartData && <Line data={chartData} options={chartOptions} />}
                  </div>

                  {/* PLC Snapshot */}
                  <div className="mb-6">
                    <h3 className="font-semibold mb-2">PLC/State Snapshot</h3>
                    <pre className="bg-gray-50 p-3 rounded text-sm overflow-x-auto">
                      {JSON.stringify(selectedMer.plc_snapshot, null, 2)}
                    </pre>
                  </div>

                  {/* Validation Controls */}
                  <div>
                    <h3 className="font-semibold mb-2">Validation Actions</h3>
                    <div className="flex gap-2 mb-4">
                      <button
                        onClick={() => handleValidation(selectedMer.id, 'confirm')}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Confirm Issue
                      </button>
                      <button
                        onClick={() => handleValidation(selectedMer.id, 'false_alarm')}
                        className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                      >
                        False Alarm
                      </button>
                      <button
                        onClick={() => handleValidation(selectedMer.id, 'work_order')}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        Work Order Created
                      </button>
                    </div>
                    <textarea
                      placeholder="Add notes about corrective action..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                    />
                  </div>
                </div>
              ) : (
                <div className="p-6 text-center text-gray-700">
                  Select an MER to view details
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}