'use client';

import { useState, useEffect } from 'react';

interface Asset {
  asset_id: string;
  name: string;
  location: string;
  model: string;
  safety_rules: string[];
  sensor_mappings: {
    sensor_tag: string;
    sensor_type: string;
    description: string;
  }[];
}

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<Partial<Asset>>({
    asset_id: '',
    name: '',
    location: '',
    model: '',
    safety_rules: [],
    sensor_mappings: []
  });
  const [loading, setLoading] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchAssets();
  }, []);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      // Mock data for now - in real implementation, fetch from API
      const mockAssets: Asset[] = [
        {
          asset_id: 'Pump-A104',
          name: 'Main Feed Pump',
          location: 'Line 1 - Station 4',
          model: 'Centrifugal-500',
          safety_rules: ['Max pressure: 50 PSI', 'Min flow rate: 10 L/min'],
          sensor_mappings: [
            { sensor_tag: 'Temp_Pump_A104', sensor_type: 'temperature', description: 'Motor temperature' },
            { sensor_tag: 'Vib_X_A104', sensor_type: 'vibration', description: 'Vibration X-axis' },
            { sensor_tag: 'Vib_Y_A104', sensor_type: 'vibration', description: 'Vibration Y-axis' },
            { sensor_tag: 'Current_A104', sensor_type: 'current', description: 'Motor current' }
          ]
        },
        {
          asset_id: 'Motor-B205',
          name: 'Conveyor Motor',
          location: 'Line 2 - Station 5',
          model: 'AC-Motor-750W',
          safety_rules: ['Max temperature: 80°C', 'Nominal speed: 1800 RPM'],
          sensor_mappings: [
            { sensor_tag: 'Temp_Motor_B205', sensor_type: 'temperature', description: 'Motor temperature' },
            { sensor_tag: 'Current_B205', sensor_type: 'current', description: 'Motor current' }
          ]
        }
      ];
      setAssets(mockAssets);
    } catch (error) {
      console.error('Error fetching assets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.asset_id || !formData.name) return;

    try {
      const assetData = {
        asset_id: formData.asset_id,
        name: formData.name,
        location: formData.location || '',
        model: formData.model || '',
        safety_rules: formData.safety_rules || [],
        sensor_mappings: formData.sensor_mappings || []
      };

      const response = await fetch(`${API_BASE}/context/assets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assetData)
      });

      if (response.ok) {
        alert('Asset saved successfully');
        fetchAssets();
        resetForm();
      } else {
        alert('Error saving asset');
      }
    } catch (error) {
      console.error('Error saving asset:', error);
      alert('Error saving asset');
    }
  };

  const handleEdit = (asset: Asset) => {
    setFormData(asset);
    setIsEditing(true);
  };

  const resetForm = () => {
    setFormData({
      asset_id: '',
      name: '',
      location: '',
      model: '',
      safety_rules: [],
      sensor_mappings: []
    });
    setIsEditing(false);
  };

  const addSensorMapping = () => {
    setFormData({
      ...formData,
      sensor_mappings: [
        ...(formData.sensor_mappings || []),
        { sensor_tag: '', sensor_type: '', description: '' }
      ]
    });
  };

  const updateSensorMapping = (index: number, field: string, value: string) => {
    const mappings = [...(formData.sensor_mappings || [])];
    mappings[index] = { ...mappings[index], [field]: value };
    setFormData({ ...formData, sensor_mappings: mappings });
  };

  const removeSensorMapping = (index: number) => {
    const mappings = [...(formData.sensor_mappings || [])];
    mappings.splice(index, 1);
    setFormData({ ...formData, sensor_mappings: mappings });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Asset Configuration</h1>
          <div className="flex gap-2">
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Add New Asset
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
          <div className="text-center py-8">Loading assets...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Assets List */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Configured Assets</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {assets.map((asset) => (
                  <div
                    key={asset.asset_id}
                    className="p-4 cursor-pointer hover:bg-gray-50"
                    onClick={() => setSelectedAsset(asset)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{asset.name}</h3>
                        <p className="text-sm text-gray-900">ID: {asset.asset_id}</p>
                        <p className="text-sm text-gray-900">{asset.location}</p>
                        <p className="text-xs text-gray-800">{asset.sensor_mappings.length} sensors mapped</p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEdit(asset);
                        }}
                        className="px-3 py-1 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600"
                      >
                        Edit
                      </button>
                    </div>
                  </div>
                ))}
                {assets.length === 0 && (
                  <div className="p-6 text-center text-gray-700">
                    No assets configured. Add your first asset above.
                  </div>
                )}
              </div>
            </div>

            {/* Asset Form */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                {isEditing ? 'Edit Asset' : 'Add New Asset'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-1">
                      Asset ID *
                    </label>
                    <input
                      type="text"
                      value={formData.asset_id || ''}
                      onChange={(e) => setFormData({ ...formData, asset_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-1">
                      Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-1">
                      Location
                    </label>
                    <input
                      type="text"
                      value={formData.location || ''}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-1">
                      Model
                    </label>
                    <input
                      type="text"
                      value={formData.model || ''}
                      onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Sensor Mappings */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-gray-900">
                      Sensor Mappings
                    </label>
                    <button
                      type="button"
                      onClick={addSensorMapping}
                      className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
                    >
                      Add Sensor
                    </button>
                  </div>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {(formData.sensor_mappings || []).map((mapping, index) => (
                      <div key={index} className="flex gap-2 items-center p-2 bg-gray-50 rounded">
                        <input
                          type="text"
                          placeholder="Sensor Tag"
                          value={mapping.sensor_tag}
                          onChange={(e) => updateSensorMapping(index, 'sensor_tag', e.target.value)}
                          className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                        />
                        <select
                          value={mapping.sensor_type}
                          onChange={(e) => updateSensorMapping(index, 'sensor_type', e.target.value)}
                          className="px-2 py-1 text-sm border border-gray-300 rounded"
                        >
                          <option value="">Type</option>
                          <option value="temperature">Temperature</option>
                          <option value="vibration">Vibration</option>
                          <option value="current">Current</option>
                          <option value="pressure">Pressure</option>
                        </select>
                        <input
                          type="text"
                          placeholder="Description"
                          value={mapping.description}
                          onChange={(e) => updateSensorMapping(index, 'description', e.target.value)}
                          className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                        />
                        <button
                          type="button"
                          onClick={() => removeSensorMapping(index)}
                          className="px-2 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    {isEditing ? 'Update Asset' : 'Create Asset'}
                  </button>
                  {isEditing && (
                    <button
                      type="button"
                      onClick={resetForm}
                      className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Asset Details Modal/Section */}
        {selectedAsset && (
          <div className="mt-8 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Asset Details: {selectedAsset.name}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Basic Information</h3>
                <div className="space-y-2 text-sm">
                  <p><strong>ID:</strong> {selectedAsset.asset_id}</p>
                  <p><strong>Location:</strong> {selectedAsset.location}</p>
                  <p><strong>Model:</strong> {selectedAsset.model}</p>
                </div>
                <h3 className="font-semibold mt-4 mb-2">Safety Rules</h3>
                <ul className="list-disc list-inside text-sm space-y-1">
                  {selectedAsset.safety_rules.map((rule, index) => (
                    <li key={index}>{rule}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Sensor Mappings</h3>
                <div className="space-y-2">
                  {selectedAsset.sensor_mappings.map((mapping, index) => (
                    <div key={index} className="p-2 bg-gray-50 rounded text-sm">
                      <div className="font-medium">{mapping.sensor_tag}</div>
                      <div className="text-gray-900">{mapping.sensor_type} - {mapping.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}