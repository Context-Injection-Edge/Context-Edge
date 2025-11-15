'use client';

import { useState, useEffect } from 'react';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

interface Threshold {
  sensor_type: string;
  warning_low: number;
  warning_high: number;
  critical_low: number;
  critical_high: number;
  unit: string;
  min_value: number;
  max_value: number;
}

export default function ThresholdsPage() {
  const [thresholds, setThresholds] = useState<Threshold[]>([]);
  const [selectedSensor, setSelectedSensor] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchThresholds();
  }, []);

  const fetchThresholds = async () => {
    setLoading(true);
    try {
      // Mock data for now - in real implementation, fetch from API
      const mockThresholds: Threshold[] = [
        {
          sensor_type: 'vibration',
          warning_low: 0.5,
          warning_high: 1.5,
          critical_low: 0.2,
          critical_high: 2.0,
          unit: 'g',
          min_value: 0,
          max_value: 3
        },
        {
          sensor_type: 'temperature',
          warning_low: 60,
          warning_high: 80,
          critical_low: 50,
          critical_high: 90,
          unit: '°C',
          min_value: 0,
          max_value: 120
        },
        {
          sensor_type: 'current',
          warning_low: 8,
          warning_high: 12,
          critical_low: 6,
          critical_high: 15,
          unit: 'A',
          min_value: 0,
          max_value: 20
        }
      ];
      setThresholds(mockThresholds);
      if (mockThresholds.length > 0) {
        setSelectedSensor(mockThresholds[0].sensor_type);
      }
    } catch (error) {
      console.error('Error fetching thresholds:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateThreshold = (sensorType: string, field: keyof Threshold, value: number) => {
    setThresholds(thresholds.map(t =>
      t.sensor_type === sensorType ? { ...t, [field]: value } : t
    ));
  };

  const saveThresholds = async () => {
    try {
      const threshold = thresholds.find(t => t.sensor_type === selectedSensor);
      if (!threshold) return;

      const response = await fetch(`${API_BASE}/context/thresholds`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(threshold)
      });

      if (response.ok) {
        alert('Thresholds saved successfully');
      } else {
        alert('Error saving thresholds');
      }
    } catch (error) {
      console.error('Error saving thresholds:', error);
      alert('Error saving thresholds');
    }
  };

  const selectedThreshold = thresholds.find(t => t.sensor_type === selectedSensor);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Threshold Management</h1>
          <div className="flex gap-2">
            <button
              onClick={saveThresholds}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Save Thresholds
            </button>
            <a
              href="/admin"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Back to Admin
            </a>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8">Loading thresholds...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Sensor Selection */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Sensor Types</h2>
              <div className="space-y-2">
                {thresholds.map((threshold) => (
                  <button
                    key={threshold.sensor_type}
                    onClick={() => setSelectedSensor(threshold.sensor_type)}
                    className={`w-full text-left px-4 py-2 rounded-md transition-colors ${
                      selectedSensor === threshold.sensor_type
                        ? 'bg-blue-100 text-blue-900 border-blue-300'
                        : 'bg-gray-50 text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium capitalize">{threshold.sensor_type}</div>
                    <div className="text-sm text-gray-600">
                      Warning: {threshold.warning_low} - {threshold.warning_high} {threshold.unit}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Threshold Editor */}
            <div className="bg-white rounded-lg shadow-md p-6 lg:col-span-2">
              {selectedThreshold ? (
                <>
                  <h2 className="text-xl font-semibold text-gray-900 mb-6 capitalize">
                    {selectedThreshold.sensor_type} Thresholds
                  </h2>

                  {/* Visual Range Display */}
                  <div className="mb-8">
                    <h3 className="font-semibold mb-4">Threshold Ranges</h3>
                    <div className="relative h-8 bg-gray-200 rounded-lg overflow-hidden">
                      {/* Critical Low */}
                      <div
                        className="absolute top-0 left-0 h-full bg-red-500 opacity-75"
                        style={{
                          width: `${(selectedThreshold.critical_low / selectedThreshold.max_value) * 100}%`
                        }}
                      />
                      {/* Warning Low */}
                      <div
                        className="absolute top-0 h-full bg-yellow-500 opacity-75"
                        style={{
                          left: `${(selectedThreshold.critical_low / selectedThreshold.max_value) * 100}%`,
                          width: `${((selectedThreshold.warning_low - selectedThreshold.critical_low) / selectedThreshold.max_value) * 100}%`
                        }}
                      />
                      {/* Normal Range */}
                      <div
                        className="absolute top-0 h-full bg-green-500 opacity-75"
                        style={{
                          left: `${(selectedThreshold.warning_low / selectedThreshold.max_value) * 100}%`,
                          width: `${((selectedThreshold.warning_high - selectedThreshold.warning_low) / selectedThreshold.max_value) * 100}%`
                        }}
                      />
                      {/* Warning High */}
                      <div
                        className="absolute top-0 h-full bg-yellow-500 opacity-75"
                        style={{
                          left: `${(selectedThreshold.warning_high / selectedThreshold.max_value) * 100}%`,
                          width: `${((selectedThreshold.critical_high - selectedThreshold.warning_high) / selectedThreshold.max_value) * 100}%`
                        }}
                      />
                      {/* Critical High */}
                      <div
                        className="absolute top-0 h-full bg-red-500 opacity-75"
                        style={{
                          left: `${(selectedThreshold.critical_high / selectedThreshold.max_value) * 100}%`,
                          width: `${((selectedThreshold.max_value - selectedThreshold.critical_high) / selectedThreshold.max_value) * 100}%`
                        }}
                      />
                    </div>
                    <div className="flex justify-between text-sm text-gray-600 mt-2">
                      <span>0 {selectedThreshold.unit}</span>
                      <span>{selectedThreshold.max_value} {selectedThreshold.unit}</span>
                    </div>
                    <div className="grid grid-cols-5 text-xs text-center mt-1">
                      <span className="text-red-600">Critical Low</span>
                      <span className="text-yellow-600">Warning Low</span>
                      <span className="text-green-600">Normal</span>
                      <span className="text-yellow-600">Warning High</span>
                      <span className="text-red-600">Critical High</span>
                    </div>
                  </div>

                  {/* Sliders */}
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-900 mb-2">
                        Critical Low: {selectedThreshold.critical_low} {selectedThreshold.unit}
                      </label>
                      <Slider
                        min={selectedThreshold.min_value}
                        max={selectedThreshold.max_value}
                        step={0.1}
                        value={selectedThreshold.critical_low}
                        onChange={(value) => updateThreshold(selectedThreshold.sensor_type, 'critical_low', value as number)}
                        trackStyle={{ backgroundColor: '#ef4444' }}
                        handleStyle={{ borderColor: '#ef4444' }}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-900 mb-2">
                        Warning Low: {selectedThreshold.warning_low} {selectedThreshold.unit}
                      </label>
                      <Slider
                        min={selectedThreshold.min_value}
                        max={selectedThreshold.max_value}
                        step={0.1}
                        value={selectedThreshold.warning_low}
                        onChange={(value) => updateThreshold(selectedThreshold.sensor_type, 'warning_low', value as number)}
                        trackStyle={{ backgroundColor: '#eab308' }}
                        handleStyle={{ borderColor: '#eab308' }}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-900 mb-2">
                        Warning High: {selectedThreshold.warning_high} {selectedThreshold.unit}
                      </label>
                      <Slider
                        min={selectedThreshold.min_value}
                        max={selectedThreshold.max_value}
                        step={0.1}
                        value={selectedThreshold.warning_high}
                        onChange={(value) => updateThreshold(selectedThreshold.sensor_type, 'warning_high', value as number)}
                        trackStyle={{ backgroundColor: '#eab308' }}
                        handleStyle={{ borderColor: '#eab308' }}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-900 mb-2">
                        Critical High: {selectedThreshold.critical_high} {selectedThreshold.unit}
                      </label>
                      <Slider
                        min={selectedThreshold.min_value}
                        max={selectedThreshold.max_value}
                        step={0.1}
                        value={selectedThreshold.critical_high}
                        onChange={(value) => updateThreshold(selectedThreshold.sensor_type, 'critical_high', value as number)}
                        trackStyle={{ backgroundColor: '#ef4444' }}
                        handleStyle={{ borderColor: '#ef4444' }}
                      />
                    </div>
                  </div>

                  {/* Current Values */}
                  <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-semibold mb-2">Current Threshold Values</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>Critical Low: <span className="font-mono">{selectedThreshold.critical_low}</span></div>
                      <div>Warning Low: <span className="font-mono">{selectedThreshold.warning_low}</span></div>
                      <div>Warning High: <span className="font-mono">{selectedThreshold.warning_high}</span></div>
                      <div>Critical High: <span className="font-mono">{selectedThreshold.critical_high}</span></div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center text-gray-700 py-8">
                  Select a sensor type to configure thresholds
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}