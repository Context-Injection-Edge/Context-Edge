'use client';

import { useState } from 'react';

// ============================================================================
// TYPES
// ============================================================================

interface DiscoveredDevice {
  ip: string;
  port: number;
  protocol: string;
  vendor: string;
  model: string;
  device_type: string;
  recommended_template: string;
  server_url?: string;
  base_url?: string;
}

interface DeviceTemplate {
  template_id: string;
  vendor: string;
  model: string;
  protocol: string;
  device_type: string;
  default_config: any;
  sensor_mappings: any;
  description: string;
}

interface TestResult {
  success: boolean;
  sample_data?: any;
  message?: string;
  error?: string;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DeviceSetupWizard() {
  // Wizard state
  const [step, setStep] = useState(1);
  const [isScanning, setIsScanning] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Data state
  const [subnet, setSubnet] = useState('192.168.1.0/24');
  const [discoveredDevices, setDiscoveredDevices] = useState<DiscoveredDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<DiscoveredDevice | null>(null);
  const [deviceTemplate, setDeviceTemplate] = useState<DeviceTemplate | null>(null);
  const [deviceName, setDeviceName] = useState('');
  const [sensorMappings, setSensorMappings] = useState<any>({});
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [liveData, setLiveData] = useState<any[]>([]);

  // ============================================================================
  // STEP 1: NETWORK SCAN
  // ============================================================================

  const scanNetwork = async () => {
    setIsScanning(true);
    setDiscoveredDevices([]);

    try {
      const response = await fetch('http://localhost:5000/api/admin/devices/scan-network', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subnet: subnet,
          protocols: ['modbus', 'opcua', 'http']
        })
      });

      const data = await response.json();

      if (data.success) {
        setDiscoveredDevices(data.devices);
        setStep(2);
      } else {
        alert('Network scan failed');
      }
    } catch (error) {
      console.error('Scan error:', error);
      alert('Network scan failed: ' + error);
    } finally {
      setIsScanning(false);
    }
  };

  // ============================================================================
  // STEP 2: DEVICE SELECTION
  // ============================================================================

  const selectDevice = async (device: DiscoveredDevice) => {
    setSelectedDevice(device);

    // Auto-generate device name
    setDeviceName(`${device.vendor} ${device.model} - ${device.ip}`);

    // Load template if available
    if (device.recommended_template) {
      try {
        const response = await fetch(
          `http://localhost:5000/api/admin/templates/${device.recommended_template}`
        );
        const template = await response.json();

        setDeviceTemplate(template);
        setSensorMappings(template.sensor_mappings || {});
      } catch (error) {
        console.error('Failed to load template:', error);
      }
    }

    setStep(3);
  };

  // ============================================================================
  // STEP 3: CONFIGURE SENSORS
  // ============================================================================

  const toggleSensor = (sensorName: string) => {
    const newMappings = { ...sensorMappings };
    if (newMappings[sensorName]) {
      delete newMappings[sensorName];
    } else if (deviceTemplate?.sensor_mappings[sensorName]) {
      newMappings[sensorName] = deviceTemplate.sensor_mappings[sensorName];
    }
    setSensorMappings(newMappings);
  };

  // ============================================================================
  // STEP 4: TEST CONNECTION
  // ============================================================================

  const testConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    setLiveData([]);

    try {
      const response = await fetch('http://localhost:5000/api/admin/devices/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device: selectedDevice,
          config: {
            sensor_mappings: sensorMappings
          }
        })
      });

      const result = await response.json();
      setTestResult(result);

      // If successful, simulate live data stream
      if (result.success && result.sample_data) {
        const timestamp = new Date().toLocaleTimeString();
        setLiveData([
          { time: timestamp, ...result.sample_data }
        ]);

        // Add a few more data points for demo
        setTimeout(() => {
          const timestamp2 = new Date().toLocaleTimeString();
          setLiveData(prev => [...prev, { time: timestamp2, ...result.sample_data }]);
        }, 1000);

        setTimeout(() => {
          const timestamp3 = new Date().toLocaleTimeString();
          setLiveData(prev => [...prev, { time: timestamp3, ...result.sample_data }]);
        }, 2000);
      }

      if (result.success) {
        setStep(4);
      }
    } catch (error) {
      console.error('Test error:', error);
      setTestResult({
        success: false,
        error: String(error)
      });
    } finally {
      setIsTesting(false);
    }
  };

  // ============================================================================
  // STEP 5: SAVE CONFIGURATION
  // ============================================================================

  const saveConfiguration = async () => {
    setIsSaving(true);

    try {
      const response = await fetch('http://localhost:5000/api/admin/devices/configs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: deviceName,
          template_id: deviceTemplate?.template_id || null,
          protocol: selectedDevice?.protocol,
          host: selectedDevice?.ip,
          port: selectedDevice?.port,
          config: deviceTemplate?.default_config || {},
          sensor_mappings: sensorMappings,
          enabled: true
        })
      });

      const result = await response.json();

      if (response.ok) {
        alert('✅ Device configured successfully!\n\nNo restart needed - hot reload will activate in 5 seconds!');
        // Redirect to devices list
        window.location.href = '/admin/devices';
      } else {
        alert('Failed to save configuration: ' + result.detail);
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('Failed to save configuration: ' + error);
    } finally {
      setIsSaving(false);
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Device Setup Wizard
          </h1>
          <p className="text-gray-600">
            Add new industrial devices to Context Edge in 3 minutes
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {[
              { num: 1, label: 'Scan Network' },
              { num: 2, label: 'Select Device' },
              { num: 3, label: 'Configure' },
              { num: 4, label: 'Test & Save' }
            ].map((s, idx) => (
              <div key={s.num} className="flex items-center flex-1">
                <div className="flex items-center">
                  <div
                    className={`
                      w-10 h-10 rounded-full flex items-center justify-center
                      font-bold text-lg
                      ${step >= s.num
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-300 text-gray-600'
                      }
                    `}
                  >
                    {s.num}
                  </div>
                  <span className="ml-3 font-medium text-gray-700">
                    {s.label}
                  </span>
                </div>
                {idx < 3 && (
                  <div
                    className={`
                      flex-1 h-1 mx-4
                      ${step > s.num ? 'bg-blue-600' : 'bg-gray-300'}
                    `}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* STEP 1: SCAN NETWORK */}
          {step === 1 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">
                Step 1: Discover Devices on Your Network
              </h2>
              <p className="text-gray-600 mb-6">
                Automatically scan your factory network to find compatible devices.
                This will detect PLCs, MES servers, and other industrial equipment.
              </p>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Network Subnet (CIDR notation)
                </label>
                <input
                  type="text"
                  value={subnet}
                  onChange={(e) => setSubnet(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="192.168.1.0/24"
                />
                <p className="text-sm text-gray-500 mt-2">
                  Example: 192.168.1.0/24 scans IPs from 192.168.1.1 to 192.168.1.254
                </p>
              </div>

              <button
                onClick={scanNetwork}
                disabled={isScanning}
                className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isScanning ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Scanning Network...
                  </>
                ) : (
                  <>
                    🔍 Scan Network
                  </>
                )}
              </button>
            </div>
          )}

          {/* STEP 2: SELECT DEVICE */}
          {step === 2 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">
                Step 2: Select Device
              </h2>
              <p className="text-gray-600 mb-6">
                Found {discoveredDevices.length} devices on your network. Select one to configure.
              </p>

              {discoveredDevices.length === 0 ? (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-yellow-800">
                    No devices found. Make sure devices are powered on and connected to the network.
                  </p>
                  <button
                    onClick={() => setStep(1)}
                    className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
                  >
                    ← Back to scan
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {discoveredDevices.map((device, idx) => (
                    <div
                      key={idx}
                      className="border border-gray-200 rounded-lg p-6 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer"
                      onClick={() => selectDevice(device)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-2xl">
                              {device.protocol === 'modbus_tcp' && '🔌'}
                              {device.protocol === 'opcua' && '🌐'}
                              {device.protocol === 'http' && '☁️'}
                            </span>
                            <div>
                              <h3 className="text-xl font-bold text-gray-900">
                                {device.vendor} {device.model}
                              </h3>
                              <p className="text-sm text-gray-600">
                                {device.ip}:{device.port} • {device.protocol.toUpperCase()}
                              </p>
                            </div>
                          </div>
                          {device.recommended_template && (
                            <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                              ✓ Template available
                            </span>
                          )}
                        </div>
                        <button className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700">
                          Add Device →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* STEP 3: CONFIGURE SENSORS */}
          {step === 3 && selectedDevice && (
            <div>
              <h2 className="text-2xl font-bold mb-4">
                Step 3: Configure Sensors
              </h2>
              <p className="text-gray-600 mb-6">
                Select which sensors to read from this device. Pre-configured based on {deviceTemplate?.vendor} {deviceTemplate?.model} template.
              </p>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Device Name
                </label>
                <input
                  type="text"
                  value={deviceName}
                  onChange={(e) => setDeviceName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Line 1 Assembly PLC"
                />
              </div>

              <div className="grid grid-cols-2 gap-8">
                {/* Available Sensors */}
                <div>
                  <h3 className="font-bold text-lg mb-4">Available Sensors</h3>
                  <div className="space-y-2">
                    {deviceTemplate && Object.keys(deviceTemplate.sensor_mappings).map((sensorName) => {
                      const isSelected = sensorName in sensorMappings;
                      const sensor = deviceTemplate.sensor_mappings[sensorName];

                      return (
                        <div
                          key={sensorName}
                          onClick={() => toggleSensor(sensorName)}
                          className={`
                            p-4 rounded-lg border-2 cursor-pointer transition-all
                            ${isSelected
                              ? 'bg-green-50 border-green-500'
                              : 'bg-white border-gray-200 hover:border-gray-400'
                            }
                          `}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="font-semibold capitalize">
                                {sensorName.replace(/_/g, ' ')}
                              </div>
                              <div className="text-sm text-gray-900">
                                {sensor.unit && `Unit: ${sensor.unit}`}
                                {sensor.address && ` • Reg: ${sensor.address}`}
                                {sensor.node_id && ` • Node: ${sensor.node_id}`}
                              </div>
                            </div>
                            <div>
                              {isSelected ? (
                                <span className="text-green-600 text-xl">✓</span>
                              ) : (
                                <span className="text-gray-400 text-xl">+</span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Selected Sensors Summary */}
                <div>
                  <h3 className="font-bold text-lg mb-4">
                    Selected Sensors ({Object.keys(sensorMappings).length})
                  </h3>
                  {Object.keys(sensorMappings).length === 0 ? (
                    <div className="text-gray-900 italic">
                      Click sensors on the left to select them
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {Object.entries(sensorMappings).map(([name, config]: [string, any]) => (
                        <div key={name} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                          <div className="font-semibold capitalize">{name.replace(/_/g, ' ')}</div>
                          <div className="text-sm text-gray-900">
                            {config.unit && `${config.unit}`}
                            {config.scale && ` • Scale: 1/${config.scale}`}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-8 flex gap-4">
                <button
                  onClick={() => setStep(2)}
                  className="px-6 py-2 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50"
                >
                  ← Back
                </button>
                <button
                  onClick={testConnection}
                  disabled={Object.keys(sensorMappings).length === 0 || isTesting}
                  className="bg-yellow-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-yellow-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {isTesting ? 'Testing...' : '🧪 Test Connection →'}
                </button>
              </div>
            </div>
          )}

          {/* STEP 4: TEST & SAVE */}
          {step === 4 && testResult && (
            <div>
              <h2 className="text-2xl font-bold mb-4">
                Step 4: Connection Test Results
              </h2>

              {testResult.success ? (
                <>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="text-4xl">✅</span>
                      <div>
                        <h3 className="text-xl font-bold text-green-800">
                          Connection Successful!
                        </h3>
                        <p className="text-green-700">
                          Reading live data from {selectedDevice?.ip}
                        </p>
                      </div>
                    </div>

                    {/* Live Data Stream */}
                    <div className="bg-white rounded-lg p-4">
                      <h4 className="font-semibold mb-3">Live Data Stream:</h4>
                      <div className="space-y-2 font-mono text-sm">
                        {liveData.map((data, idx) => (
                          <div key={idx} className="flex items-center gap-4">
                            <span className="text-gray-500">{data.time}</span>
                            {Object.entries(data).filter(([key]) => key !== 'time').map(([key, value]) => (
                              <span key={key} className="text-green-600">
                                {key}: {typeof value === 'number' ? value.toFixed(2) : value}
                              </span>
                            ))}
                            <span className="text-green-600">✓</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <button
                      onClick={() => setStep(3)}
                      className="px-6 py-2 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50"
                    >
                      ← Back to Configuration
                    </button>
                    <button
                      onClick={saveConfiguration}
                      disabled={isSaving}
                      className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 flex-1"
                    >
                      {isSaving ? 'Saving...' : '💾 Save Configuration & Go Live!'}
                    </button>
                  </div>
                </>
              ) : (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <h3 className="text-xl font-bold text-red-800 mb-2">
                    Connection Failed
                  </h3>
                  <p className="text-red-700 mb-4">
                    {testResult.error || testResult.message}
                  </p>
                  <button
                    onClick={() => setStep(3)}
                    className="bg-red-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-red-700"
                  >
                    ← Back to Configuration
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
