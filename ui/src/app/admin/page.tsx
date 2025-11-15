'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface MetadataPayload {
  id?: number;
  cid: string;
  metadata: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export default function AdminPage() {
  const [payloads, setPayloads] = useState<MetadataPayload[]>([]);
  const [formData, setFormData] = useState({
    cid: '',
    metadata: '{}'
  });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchPayloads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchPayloads = async () => {
    try {
      const response = await fetch(`${API_BASE}/context`);
      if (response.ok) {
        const data = await response.json();
        setPayloads(data);
      } else {
        console.error('Failed to fetch payloads:', response.statusText);
        setPayloads([]);
      }
    } catch (error) {
      console.error('Error fetching payloads:', error);
      // Show empty state if API is not available
      setPayloads([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const metadata = JSON.parse(formData.metadata);
      const payload = { cid: formData.cid, metadata };

      if (editingId) {
        // Update
        await fetch(`${API_BASE}/context/${formData.cid}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } else {
        // Create
        await fetch(`${API_BASE}/context`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      setFormData({ cid: '', metadata: '{}' });
      setEditingId(null);
      fetchPayloads();
    } catch (error) {
      console.error('Error saving payload:', error);
      alert('Error saving payload. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (payload: MetadataPayload) => {
    setFormData({
      cid: payload.cid,
      metadata: JSON.stringify(payload.metadata, null, 2)
    });
    setEditingId(payload.id || null);
  };

  const handleDelete = async (cid: string) => {
    if (!confirm('Are you sure you want to delete this payload?')) return;

    try {
      await fetch(`${API_BASE}/context/${cid}`, { method: 'DELETE' });
      fetchPayloads();
    } catch (error) {
      console.error('Error deleting payload:', error);
    }
  };

  const handleCsvImport = async () => {
    if (!csvFile) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', csvFile);

      const response = await fetch(`${API_BASE}/context/bulk-import`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        alert(result.message + (result.errors ? `\n\nErrors:\n${result.errors.join('\n')}` : ''));
        setCsvFile(null);
        fetchPayloads();
      } else {
        const error = await response.text();
        alert(`Error importing CSV: ${error}`);
      }
    } catch (error) {
      console.error('Error importing CSV:', error);
      alert('Error importing CSV. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Context Edge Admin</h1>
          <Link
            href="/"
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Back to Home
          </Link>
        </div>

        {/* Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <a
            href="/admin/mer-reports"
            className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border-l-4 border-blue-500"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">📋 MER Reports</h3>
            <p className="text-sm text-gray-600">View and validate Maintenance Event Records</p>
          </a>
          <a
            href="/admin/thresholds"
            className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border-l-4 border-yellow-500"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">⚙️ Thresholds</h3>
            <p className="text-sm text-gray-600">Configure sensor warning and critical limits</p>
          </a>
          <a
            href="/admin/assets"
            className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border-l-4 border-green-500"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">🏭 Assets</h3>
            <p className="text-sm text-gray-600">Manage asset master data and sensor mappings</p>
          </a>
          <a
            href="/admin/models"
            className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border-l-4 border-purple-500"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">🤖 ML Models</h3>
            <p className="text-sm text-gray-600">Deploy and manage AI models across edge devices</p>
          </a>
          <a
            href="/admin/feedback"
            className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border-l-4 border-red-500"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">💬 Feedback Queue</h3>
            <p className="text-sm text-gray-600">Validate low-confidence predictions for retraining</p>
          </a>
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-lg shadow-md border-l-4 border-indigo-500">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">📊 Metadata Management</h3>
            <p className="text-sm text-gray-600">Create and manage context metadata (below)</p>
          </div>
        </div>

        {/* Form */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            {editingId ? 'Edit Metadata Payload' : 'Create New Metadata Payload'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Context ID (CID)
              </label>
              <input
                type="text"
                value={formData.cid}
                onChange={(e) => setFormData({ ...formData, cid: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Metadata (JSON)
              </label>
              <textarea
                value={formData.metadata}
                onChange={(e) => setFormData({ ...formData, metadata: e.target.value })}
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                placeholder='{"product_name": "Widget A", "batch_number": "BATCH001"}'
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Saving...' : (editingId ? 'Update' : 'Create')}
              </button>
              {editingId && (
                <button
                  type="button"
                  onClick={() => {
                    setFormData({ cid: '', metadata: '{}' });
                    setEditingId(null);
                  }}
                  className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>

        {/* CSV Import */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Bulk Import from CSV</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                CSV File (columns: cid, metadata_json)
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
              />
            </div>
            <button
              onClick={handleCsvImport}
              disabled={!csvFile || loading}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? 'Importing...' : 'Import CSV'}
            </button>
          </div>
        </div>

        {/* Payloads List */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Metadata Payloads</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {payloads.map((payload) => (
              <div key={payload.id} className="p-6">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900">CID: {payload.cid}</h3>
                    <pre className="mt-2 text-sm text-gray-800 bg-gray-50 p-3 rounded overflow-x-auto">
                      {JSON.stringify(payload.metadata, null, 2)}
                    </pre>
                    <p className="mt-2 text-sm text-gray-700">
                      Created: {new Date(payload.created_at || '').toLocaleString()}
                    </p>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => handleEdit(payload)}
                      className="px-3 py-1 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(payload.cid)}
                      className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {payloads.length === 0 && (
              <div className="p-6 text-center text-gray-700">
                No metadata payloads found. Create your first one above.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}