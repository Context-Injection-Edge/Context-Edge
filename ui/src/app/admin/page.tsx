






'use client';







import { useState, useEffect } from 'react';



import Link from 'next/link';







// ============================================================================



// TYPES



// ============================================================================



interface MetadataPayload {



  id?: number;



  cid: string;



  metadata: Record<string, unknown>;



  created_at?: string;



  updated_at?: string;



}







// ============================================================================



// MAIN COMPONENT



// ============================================================================



export default function AdminPage() {



  const [payloads, setPayloads] = useState<MetadataPayload[]>([]);



  const [formData, setFormData] = useState({



    cid: '',



    metadata: '{}'



  });



  const [editingId, setEditingId] = useState<number | null>(null);



  const [loading, setLoading] = useState(false);



  const [csvFile, setCsvFile] = useState<File | null>(null);



  const [showMetadata, setShowMetadata] = useState(false);







  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';







  useEffect(() => {



    if (showMetadata) {



      fetchPayloads();



    }



  }, [showMetadata]);







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



        await fetch(`${API_BASE}/context/${formData.cid}`, {



          method: 'PUT',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify(payload)



        });



      } else {



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



    setShowMetadata(true);



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



    <div className="max-w-7xl mx-auto space-y-8">



      <div className="bg-gray-800 shadow-md rounded-lg p-8">



        <h1 className="text-4xl font-bold text-white mb-2">Admin Dashboard</h1>



        <p className="text-lg text-gray-300 mb-6">



          Welcome to the unified dashboard for the Context Edge platform.



        </p>



        



        {/* Navigation Cards */}



        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">



          <Link href="/admin/devices" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-lg transition text-center flex flex-col items-center justify-center">



            <span className="text-3xl mb-2">🏭</span>



            <span>Manage Devices</span>



          </Link>



          <Link href="/admin/health" className="bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-6 rounded-lg transition text-center flex flex-col items-center justify-center">



            <span className="text-3xl mb-2">🚦</span>



            <span>System Health</span>



          </Link>



          <Link href="/admin/recommendations" className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-4 px-6 rounded-lg transition text-center flex flex-col items-center justify-center">



            <span className="text-3xl mb-2">💡</span>



            <span>View Recommendations</span>



          </Link>



        </div>



      </div>







      {/* Metadata Management Section */}



      <div className="bg-gray-800 shadow-md rounded-lg">



        <button



          onClick={() => setShowMetadata(!showMetadata)}



          className="w-full p-6 text-left text-2xl font-bold text-white focus:outline-none"



        >



          <span className="mr-4">{showMetadata ? '▼' : '►'}</span>



          Metadata Management



        </button>







        {showMetadata && (



          <div className="p-8 pt-0 space-y-8">



            {/* Form */}



            <div className="bg-gray-900 p-6 rounded-lg shadow-md">



              <h2 className="text-xl font-semibold text-white mb-4">



                {editingId ? 'Edit Metadata Payload' : 'Create New Metadata Payload'}



              </h2>



              <form onSubmit={handleSubmit} className="space-y-4">



                <div>



                  <label className="block text-sm font-medium text-gray-300 mb-1">



                    Context ID (CID)



                  </label>



                  <input



                    type="text"



                    value={formData.cid}



                    onChange={(e) => setFormData({ ...formData, cid: e.target.value })}



                    className="w-full px-3 py-2 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-white bg-gray-700"



                    required



                  />



                </div>



                <div>



                  <label className="block text-sm font-medium text-gray-300 mb-1">



                    Metadata (JSON)



                  </label>



                  <textarea



                    value={formData.metadata}



                    onChange={(e) => setFormData({ ...formData, metadata: e.target.value })}



                    rows={6}



                    className="w-full px-3 py-2 border border-gray-600 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-white bg-gray-700"



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



                      className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"



                    >



                      Cancel



                    </button>



                  )}



                </div>



              </form>



            </div>







            {/* CSV Import */}



            <div className="bg-gray-900 p-6 rounded-lg shadow-md">



              <h2 className="text-xl font-semibold text-white mb-4">Bulk Import from CSV</h2>



              <div className="space-y-4">



                <div>



                  <label className="block text-sm font-medium text-gray-300 mb-1">



                    CSV File (columns: cid, metadata_json)



                  </label>



                  <input



                    type="file"



                    accept=".csv"



                    onChange={(e) => setCsvFile(e.target.files?.[0] || null)}



                    className="w-full px-3 py-2 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-white bg-gray-700"



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



            <div className="bg-gray-900 rounded-lg shadow-md">



              <div className="px-6 py-4 border-b border-gray-700">



                <h2 className="text-xl font-semibold text-white">Metadata Payloads</h2>



              </div>



              <div className="divide-y divide-gray-700">



                {payloads.map((payload) => (



                  <div key={payload.id} className="p-6">



                    <div className="flex justify-between items-start">



                      <div className="flex-1">



                        <h3 className="text-lg font-medium text-white">CID: {payload.cid}</h3>



                        <pre className="mt-2 text-sm text-gray-200 bg-gray-800 p-3 rounded overflow-x-auto">



                          {JSON.stringify(payload.metadata, null, 2)}



                        </pre>



                        <p className="mt-2 text-sm text-gray-400">



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



                  <div className="p-6 text-center text-gray-400">



                    No metadata payloads found. Create one or click the header to fetch.



                  </div>



                )}



              </div>



            </div>



          </div>



        )}



      </div>



    </div>



  );



}




