'use client';

export default function DownloadsPage() {
  const downloads = [
    {
      name: 'Edge Device SDK',
      description: 'Python SDK for deploying Context Edge on NVIDIA Jetson devices',
      type: 'Python Package',
      version: '0.1.0',
      install: 'pip install context-edge-sdk',
      downloadUrl: '#',
      docsUrl: '/docs/edge-sdk'
    },
    {
      name: 'Context Service',
      description: 'Docker Compose setup for Context Service (PostgreSQL + Redis + FastAPI)',
      type: 'Docker Compose',
      version: '1.0.0',
      install: 'docker-compose up -d',
      downloadUrl: 'https://github.com/yourusername/context-edge/archive/refs/heads/main.zip',
      docsUrl: '/docs/context-service'
    },
    {
      name: 'Data Ingestion Service',
      description: 'LDO ingestion and storage service',
      type: 'Docker Image',
      version: '1.0.0',
      install: 'docker pull context-edge/data-ingestion:latest',
      downloadUrl: '#',
      docsUrl: '/docs/data-ingestion'
    },
    {
      name: 'Sample Demo Data',
      description: 'Sample QR codes and metadata for testing',
      type: 'CSV',
      version: '1.0.0',
      install: 'Download and import via Admin Panel',
      downloadUrl: '#',
      docsUrl: '/docs/demo'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-600 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-center">Downloads</h1>
          <p className="text-xl text-center mt-4">
            Get started with Context Edge - Download SDKs, Docker images, and documentation
          </p>
        </div>
      </header>

      {/* Downloads Grid */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {downloads.map((download, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-2xl font-semibold text-gray-900">{download.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">{download.type} • v{download.version}</p>
                    <p className="text-gray-700 mt-3">{download.description}</p>

                    {/* Install Command */}
                    <div className="mt-4 bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm overflow-x-auto">
                      {download.install}
                    </div>

                    {/* Action Buttons */}
                    <div className="mt-4 flex gap-3">
                      <a
                        href={download.downloadUrl}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                      >
                        Download
                      </a>
                      <a
                        href={download.docsUrl}
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition"
                      >
                        Documentation
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Quick Start Guide</h2>

          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold mb-2">1. Deploy Context Service</h3>
              <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-sm overflow-x-auto">
                git clone https://github.com/yourusername/context-edge.git<br/>
                cd context-edge<br/>
                docker-compose up -d
              </div>
            </div>

            <div>
              <h3 className="text-xl font-semibold mb-2">2. Access the Admin Panel</h3>
              <p className="text-gray-700 mb-2">
                Navigate to <a href="http://localhost:3000/admin" className="text-blue-600 hover:underline">http://localhost:3000/admin</a> and create your first metadata payload
              </p>
            </div>

            <div>
              <h3 className="text-xl font-semibold mb-2">3. Install Edge SDK</h3>
              <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-sm overflow-x-auto">
                pip install context-edge-sdk
              </div>
            </div>

            <div>
              <h3 className="text-xl font-semibold mb-2">4. Run Demo</h3>
              <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-sm overflow-x-auto">
                context-edge-demo
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Support */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Need Help?</h2>
            <p className="text-gray-700 mb-4">
              Check out our comprehensive documentation or reach out to our support team.
            </p>
            <div className="flex gap-4">
              <a href="/docs" className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                View Documentation
              </a>
              <a href="mailto:support@context-edge.com" className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
                Contact Support
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
