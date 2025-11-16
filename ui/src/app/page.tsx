'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

export default function Home() {
  const diagramRef = useRef<HTMLDivElement>(null);
  const [isMounted, setIsMounted] = useState(false);

  // Only render Mermaid on client (prevents hydration mismatch)
  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted) return;
    // Initialize Mermaid with proper config
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      flowchart: { useMaxWidth: true }
    });

    // Patent Figure 1: System Architecture
    const architectureDiagram = `graph TB
    subgraph CML["Context Management Layer"]
        AI[Admin Interface]
        RMD[Rich Metadata Database]
        PAL[provides authoritative labels]
        CSA[Context Service API]
        AI --> RMD
        RMD --> PAL
        PAL --> CSA
    end

    subgraph PW["Physical World"]
        QR[Physical QR Code on Object]
    end

    subgraph EPL["Edge Processing Layer"]
        VSE[Vision/Sensor Engine]
        SDS[Sensor Data Stream]
        CD[Context Decoder]
        VSE --> SDS
        VSE --> CD
        CIM{Context Injection<br/>Module CIM<br/>PATENTED}
        SDS --> CIM
        CD --> CIM
    end

    QR --> CD
    CSA -->|CID Query| CD
    CSA -->|Rich Metadata Payload| CIM

    CIM --> LDO[Labeled Data Object LDO]

    subgraph DIL["Data Ingestion & Intelligence Layer"]
        OPS[Real-Time Operator Dashboard]
        QC[Quality Control & Engineering Analytics]
        ML[ML Training & Data Science Pipeline]
        STORE[Data Lake Storage & Traceability]
    end

    LDO --> OPS
    LDO --> QC
    LDO --> ML
    LDO --> STORE

    style CIM fill:#ffd700,stroke:#333,stroke-width:3px
    style PAL fill:#e8e8e8
    style SDS fill:#e8e8e8
    style OPS fill:#e3f2fd
    style QC fill:#e8f5e9
    style ML fill:#f3e5f5`;

    const renderDiagram = async () => {
      if (diagramRef.current) {
        try {
          const { svg } = await mermaid.render('patentDiagram', architectureDiagram);
          diagramRef.current.innerHTML = svg;
        } catch (error) {
          console.error('Mermaid render error:', error);
          diagramRef.current.innerHTML = '<p class="text-red-600">Diagram rendering error. Please refresh the page.</p>';
        }
      }
    };
    renderDiagram();
  }, [isMounted]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center mb-12">
            <div>
              <div className="inline-block px-3 py-1 bg-yellow-400 text-gray-900 rounded-full text-xs font-bold mb-3">
                🏆 PATENTED TECHNOLOGY
              </div>
              <h1 className="text-5xl font-bold mb-3">
                Context Edge
              </h1>
              <p className="text-xl text-blue-100">
                Ground-Truth Injection at the Edge—Zero-Effort ML Training Data
              </p>
            </div>
            <div className="flex gap-3">
              <a
                href="/downloads"
                className="px-4 py-2 bg-white text-blue-600 rounded-md hover:bg-gray-100 transition-colors"
              >
                Downloads
              </a>
              <a
                href="/admin"
                className="px-4 py-2 bg-blue-700 text-white border-2 border-white rounded-md hover:bg-blue-800 transition-colors"
              >
                Admin Panel
              </a>
            </div>
          </div>

          {/* Hero Value Proposition */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            {/* Left: Main Message */}
            <div>
              <h2 className="text-3xl font-bold mb-6 leading-tight">
                Industrial Edge AI Platform<br/>
                for Smart Manufacturing
              </h2>
              <p className="text-lg text-blue-100 mb-8 leading-relaxed">
                Context Edge is an <strong className="text-white">industrial edge AI platform</strong> that runs machine learning
                models directly at the edge, synchronously fusing <strong className="text-white">physical context identifiers</strong> (QR, RFID, OCR, barcodes)
                with <strong className="text-white">real-time video and sensor streams</strong>. Deploy AI for quality control, defect detection,
                and process optimization—while automatically generating perfectly labeled training data for continuous learning.
                No cloud dependency. Sub-100ms decisions where it matters.
              </p>

              {/* Key Benefits */}
              <div className="space-y-4 mb-8">
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-green-400 rounded-full flex items-center justify-center mr-3 mt-1">
                    <span className="text-green-900 text-sm">✓</span>
                  </div>
                  <div>
                    <strong className="text-white">Real-Time AI Inference:</strong>
                    <span className="text-blue-100"> Quality control • Defect detection • Sub-100ms at edge • Works air-gapped</span>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-green-400 rounded-full flex items-center justify-center mr-3 mt-1">
                    <span className="text-green-900 text-sm">✓</span>
                  </div>
                  <div>
                    <strong className="text-white">Automated Training Data:</strong>
                    <span className="text-blue-100"> 100% accurate labels • Zero manual work • Continuous learning</span>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-green-400 rounded-full flex items-center justify-center mr-3 mt-1">
                    <span className="text-green-900 text-sm">✓</span>
                  </div>
                  <div>
                    <strong className="text-white">Multi-Source Fusion:</strong>
                    <span className="text-blue-100"> QR, RFID, OCR, barcodes + video/sensor streams synchronized at edge</span>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-green-400 rounded-full flex items-center justify-center mr-3 mt-1">
                    <span className="text-green-900 text-sm">✓</span>
                  </div>
                  <div>
                    <strong className="text-white">Production Ready:</strong>
                    <span className="text-blue-100"> Edge MLOps • Human-in-the-loop • Model deployment • Continuous monitoring</span>
                  </div>
                </div>
              </div>

              <a
                href="/downloads"
                className="inline-block px-8 py-4 bg-white text-blue-600 font-bold rounded-lg hover:bg-gray-100 transition-colors text-lg shadow-lg"
              >
                Get Started Now →
              </a>
            </div>

            {/* Right: How CIM Works */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
              <h3 className="text-2xl font-bold mb-6 text-yellow-300 text-center">How CIM Fusion Works</h3>

              {/* Step 1: Context Identifiers */}
              <div className="mb-4 text-center">
                <div className="text-sm text-blue-200 mb-2">STEP 1: Scan Context Identifier</div>
                <div className="flex flex-wrap gap-2 mb-1 justify-center">
                  <span className="px-3 py-1 bg-blue-500/50 rounded-full text-xs text-white">QR Code</span>
                  <span className="px-3 py-1 bg-blue-500/50 rounded-full text-xs text-white">RFID Tag</span>
                  <span className="px-3 py-1 bg-blue-500/50 rounded-full text-xs text-white">Barcode</span>
                  <span className="px-3 py-1 bg-blue-500/50 rounded-full text-xs text-white">OCR</span>
                  <span className="px-3 py-1 bg-blue-500/50 rounded-full text-xs text-white">NFC</span>
                </div>
                <div className="text-xs text-blue-100 mt-2">Triggers system and provides product/asset ID</div>
              </div>

              <div className="text-center text-2xl text-yellow-300 mb-3">↓</div>

              {/* Step 2: Fetch Data */}
              <div className="mb-4 text-center">
                <div className="text-sm text-blue-200 mb-2">STEP 2: Fetch Data from Multiple Sources</div>
                <div className="space-y-2">
                  <div>
                    <div className="text-xs text-blue-100 mb-1">Metadata Payloads:</div>
                    <div className="flex flex-wrap gap-1 justify-center">
                      <span className="px-2 py-1 bg-purple-500/50 rounded-full text-xs text-white">Context DB</span>
                      <span className="px-2 py-1 bg-purple-500/50 rounded-full text-xs text-white">PLM/ERP</span>
                      <span className="px-2 py-1 bg-purple-500/50 rounded-full text-xs text-white">Cloud APIs</span>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-blue-100 mb-1">Real-Time Streams:</div>
                    <div className="flex flex-wrap gap-1 justify-center">
                      <span className="px-2 py-1 bg-purple-500/50 rounded-full text-xs text-white">Video</span>
                      <span className="px-2 py-1 bg-purple-500/50 rounded-full text-xs text-white">PLC Sensors</span>
                      <span className="px-2 py-1 bg-purple-500/50 rounded-full text-xs text-white">SCADA</span>
                      <span className="px-2 py-1 bg-purple-500/50 rounded-full text-xs text-white">IoT</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-center text-2xl text-yellow-300 mb-3">↓</div>

              {/* Step 3: CIM Fusion */}
              <div className="bg-yellow-400/20 border-2 border-yellow-400 rounded-lg p-4 mb-3">
                <div className="flex items-center justify-center mb-2">
                  <div className="text-3xl mr-3">⚡</div>
                  <div className="font-bold text-yellow-300 text-lg">EDGE AI FUSION</div>
                </div>
                <div className="text-center text-white font-semibold mb-1">Context Injection Module (CIM)</div>
                <div className="text-center text-xs text-blue-200 mb-1">Patented Synchronous Data Fusion</div>
                <div className="text-center text-xs text-blue-100">Fuses: ID + Metadata + Sensor Data + Video</div>
                <div className="text-center text-xs text-blue-100 mt-1">Runs AI inference • Sub-100ms • Works air-gapped</div>
              </div>

              <div className="text-center text-2xl text-green-400 mb-3">↓</div>

              {/* Step 4: Output */}
              <div className="bg-green-500/20 border-2 border-green-400 rounded-lg p-4">
                <div className="flex items-center justify-center mb-2">
                  <div className="text-2xl mr-2">✓</div>
                  <div className="font-bold text-white">Labeled Data Objects (LDOs)</div>
                </div>
                <div className="text-center text-xs text-blue-100">
                  Perfect training data • 100% accurate labels • Zero manual work
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Why Revolutionary */}
      <section className="py-16 bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Why Context Edge is Revolutionary</h2>
            <p className="text-xl text-gray-700 max-w-3xl mx-auto">
              More than automation - Context Edge transforms how operators, engineers, and data scientists work together
            </p>
          </div>

          {/* Before vs After Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            {/* Traditional */}
            <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center text-white text-2xl mr-3">✗</div>
                <h3 className="text-2xl font-bold text-red-900">Traditional Manufacturing</h3>
              </div>
              <ul className="space-y-3 text-gray-900">
                <li className="flex items-start">
                  <span className="text-red-500 mr-2">•</span>
                  <span>Operators manually log batch numbers and product types</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-500 mr-2">•</span>
                  <span>Engineers spend weeks collecting and labeling data</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-500 mr-2">•</span>
                  <span>Quality issues discovered hours or days later</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-500 mr-2">•</span>
                  <span>PLC sensor data lacks context and meaning</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-500 mr-2">•</span>
                  <span>Data scientists can&apos;t trust data accuracy</span>
                </li>
              </ul>
            </div>

            {/* Context Edge */}
            <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white text-2xl mr-3">✓</div>
                <h3 className="text-2xl font-bold text-green-900">With Context Edge</h3>
              </div>
              <ul className="space-y-3 text-gray-900">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span><strong>Automatic labeling</strong> - QR codes provide instant context</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span><strong>Real-time insights</strong> - Engineers get immediate analytics</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span><strong>Instant alerts</strong> - Quality issues caught in real-time</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span><strong>Perfect context</strong> - Every sensor reading labeled accurately</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span><strong>100% accuracy</strong> - Ground-truth data from physical identifiers</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Key Innovations */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg p-6 shadow-lg text-center transform hover:scale-105 transition-transform">
              <div className="text-4xl mb-3">⚡</div>
              <h4 className="font-bold text-gray-900 mb-2">Edge Processing</h4>
              <p className="text-sm text-gray-700">Sub-100ms latency. Decisions at the edge, not the cloud.</p>
            </div>
            <div className="bg-white rounded-lg p-6 shadow-lg text-center transform hover:scale-105 transition-transform">
              <div className="text-4xl mb-3">🎯</div>
              <h4 className="font-bold text-gray-900 mb-2">Zero Manual Work</h4>
              <p className="text-sm text-gray-700">QR codes provide physical ground truth automatically.</p>
            </div>
            <div className="bg-white rounded-lg p-6 shadow-lg text-center transform hover:scale-105 transition-transform">
              <div className="text-4xl mb-3">🤖</div>
              <h4 className="font-bold text-gray-900 mb-2">Continuous Learning</h4>
              <p className="text-sm text-gray-700">Models improve automatically from validated production data</p>
            </div>
            <div className="bg-white rounded-lg p-6 shadow-lg text-center transform hover:scale-105 transition-transform">
              <div className="text-4xl mb-3">💰</div>
              <h4 className="font-bold text-gray-900 mb-2">Massive Savings</h4>
              <p className="text-sm text-gray-700">90% less annotation cost, 70% bandwidth reduction.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Equipment Compatibility - Compact Banner */}
      <section className="py-8 bg-gradient-to-r from-green-50 to-blue-50 border-y border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {/* Left: Headline */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white text-xl">
                ✓
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Works with Your Existing Equipment</h3>
                <p className="text-sm text-gray-600">85%+ industrial automation coverage • No rip-and-replace</p>
              </div>
            </div>

            {/* Center: Protocol List */}
            <div className="flex items-center gap-2 flex-wrap justify-center">
              <span className="px-3 py-1 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm">OPC UA</span>
              <span className="px-3 py-1 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm">Modbus TCP</span>
              <span className="px-3 py-1 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm">EtherNet/IP</span>
              <span className="px-3 py-1 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm">PROFINET</span>
              <span className="px-3 py-1 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm">Modbus RTU</span>
            </div>

            {/* Right: Link */}
            <a
              href="/downloads"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap"
            >
              View Integration Guide →
            </a>
          </div>
        </div>
      </section>

      {/* Platform Use Cases */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">One Platform, Multiple Use Cases</h2>
            <p className="text-xl text-gray-700 max-w-3xl mx-auto">
              Context Edge is a flexible industrial AI platform serving manufacturers across industries
            </p>
          </div>

          {/* Use Case Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Quality Control */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border-2 border-blue-200 hover:border-blue-400 transition-all">
              <div className="text-4xl mb-3">🎯</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Quality Control</h3>
              <p className="text-sm text-gray-700 mb-3">
                Scan part QR code → AI detects defects in real-time → Creates perfect training data automatically
              </p>
              <div className="text-xs text-blue-700 font-medium">Industries: Automotive, Electronics, Medical Devices</div>
            </div>

            {/* Predictive Maintenance */}
            <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-6 border-2 border-orange-200 hover:border-orange-400 transition-all">
              <div className="text-4xl mb-3">⚙️</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Predictive Maintenance</h3>
              <p className="text-sm text-gray-700 mb-3">
                Equipment RFID tag → Monitor vibration/temp → Alert engineer before failure → Complete incident context
              </p>
              <div className="text-xs text-orange-700 font-medium">Industries: Manufacturing, Oil & Gas, Utilities</div>
            </div>

            {/* Compliance & Traceability */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border-2 border-green-200 hover:border-green-400 transition-all">
              <div className="text-4xl mb-3">📋</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Compliance & Traceability</h3>
              <p className="text-sm text-gray-700 mb-3">
                Batch barcode → Video + sensor documentation → Complete audit trail for FDA/regulatory compliance
              </p>
              <div className="text-xs text-green-700 font-medium">Industries: Pharma, Food & Beverage, Aerospace</div>
            </div>

            {/* Process Optimization */}
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border-2 border-purple-200 hover:border-purple-400 transition-all">
              <div className="text-4xl mb-3">📊</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Process Optimization</h3>
              <p className="text-sm text-gray-700 mb-3">
                Production order QR → Monitor actual vs expected → Identify bottlenecks → Optimize throughput
              </p>
              <div className="text-xs text-purple-700 font-medium">Industries: Chemicals, Semiconductors, Food Processing</div>
            </div>

            {/* Supply Chain Visibility */}
            <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-xl p-6 border-2 border-yellow-200 hover:border-yellow-400 transition-all">
              <div className="text-4xl mb-3">🚚</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Supply Chain & Cold Chain</h3>
              <p className="text-sm text-gray-700 mb-3">
                Package RFID → Track temp/humidity/GPS → Quality verification → Claims documentation
              </p>
              <div className="text-xs text-yellow-700 font-medium">Industries: Pharma, Food, Electronics, Luxury Goods</div>
            </div>

            {/* Safety & Incidents */}
            <div className="bg-gradient-to-br from-red-50 to-rose-50 rounded-xl p-6 border-2 border-red-200 hover:border-red-400 transition-all">
              <div className="text-4xl mb-3">🛡️</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Safety & Incident Investigation</h3>
              <p className="text-sm text-gray-700 mb-3">
                Anomaly detected → Pull video + sensor data → Complete event reconstruction → Root cause analysis
              </p>
              <div className="text-xs text-red-700 font-medium">Industries: Oil & Gas, Mining, Construction</div>
            </div>
          </div>

          {/* Bottom CTA */}
          <div className="text-center mt-12">
            <p className="text-lg text-gray-700 mb-6">
              <strong>One platform.</strong> Multiple applications. Ready to transform your manufacturing operations?
            </p>
            <a
              href="/downloads"
              className="inline-block px-8 py-4 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors text-lg shadow-lg"
            >
              Get Started with Context Edge →
            </a>
          </div>
        </div>
      </section>

      {/* Project Overview */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">About Context Edge</h2>
          <p className="text-lg text-gray-900 leading-relaxed mb-4">
            <strong>Context Edge</strong> implements our patented <strong>Context Injection Module (CIM)</strong> - a revolutionary platform that fuses physical context identifiers (QR codes) with real-time sensor data at the network edge. This intelligent system serves operators with real-time monitoring, engineers with quality control insights, and data scientists with 100% accurate ML training data.
          </p>
          <p className="text-lg text-gray-900 leading-relaxed">
            <strong>Patent:</strong> &quot;System and Method for Real-Time Ground-Truth Labeling of Sensor Data Streams Using Physical Contextual Identifiers at the Network Edge&quot; - This isn&apos;t just automation, it&apos;s <strong>augmentation of human expertise with perfect data</strong>.
          </p>
        </div>
      </section>

      {/* Architecture Overview */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Three-Tier Architecture</h2>
            <p className="text-xl text-gray-700">Designed for industrial reliability and scale</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            {/* Cloud Layer */}
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 border-2 border-indigo-200 p-8 rounded-xl shadow-lg">
              <div className="text-center mb-4">
                <div className="text-5xl mb-3">☁️</div>
                <h3 className="text-2xl font-bold text-gray-900">Context Management</h3>
                <p className="text-sm text-gray-600 mt-1">Cloud / On-Premises</p>
              </div>
              <ul className="space-y-2 text-gray-900">
                <li className="flex items-start">
                  <span className="text-indigo-500 mr-2">●</span>
                  <span>Rich Metadata Database (PostgreSQL)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-indigo-500 mr-2">●</span>
                  <span>Context Service API (FastAPI)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-indigo-500 mr-2">●</span>
                  <span>High-Speed Redis Cache</span>
                </li>
                <li className="flex items-start">
                  <span className="text-indigo-500 mr-2">●</span>
                  <span>Admin Interface</span>
                </li>
              </ul>
            </div>

            {/* Edge Layer - Highlighted as the CIM */}
            <div className="bg-gradient-to-br from-yellow-50 to-amber-50 border-4 border-yellow-400 p-8 rounded-xl shadow-2xl transform scale-105">
              <div className="text-center mb-4">
                <div className="inline-block px-3 py-1 bg-yellow-400 rounded-full text-xs font-bold text-gray-900 mb-2">PATENTED</div>
                <div className="text-5xl mb-3">⚡</div>
                <h3 className="text-2xl font-bold text-gray-900">Edge Processing (CIM)</h3>
                <p className="text-sm text-gray-600 mt-1">Factory Floor</p>
              </div>
              <ul className="space-y-2 text-gray-900">
                <li className="flex items-start">
                  <span className="text-yellow-600 mr-2">●</span>
                  <span><strong>Context Injection Module</strong></span>
                </li>
                <li className="flex items-start">
                  <span className="text-yellow-600 mr-2">●</span>
                  <span>Vision Engine (Camera)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-yellow-600 mr-2">●</span>
                  <span>QR Code Decoder</span>
                </li>
                <li className="flex items-start">
                  <span className="text-yellow-600 mr-2">●</span>
                  <span>Edge AI (NVIDIA Jetson)</span>
                </li>
              </ul>
            </div>

            {/* Data Layer */}
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200 p-8 rounded-xl shadow-lg">
              <div className="text-center mb-4">
                <div className="text-5xl mb-3">📊</div>
                <h3 className="text-2xl font-bold text-gray-900">Data & Intelligence</h3>
                <p className="text-sm text-gray-600 mt-1">Cloud / Data Lake</p>
              </div>
              <ul className="space-y-2 text-gray-900">
                <li className="flex items-start">
                  <span className="text-purple-500 mr-2">●</span>
                  <span>Operator Dashboards</span>
                </li>
                <li className="flex items-start">
                  <span className="text-purple-500 mr-2">●</span>
                  <span>Engineering Analytics</span>
                </li>
                <li className="flex items-start">
                  <span className="text-purple-500 mr-2">●</span>
                  <span>ML Training Pipeline</span>
                </li>
                <li className="flex items-start">
                  <span className="text-purple-500 mr-2">●</span>
                  <span>Data Lake (S3/MinIO)</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Collapsible Technical Diagram */}
          <details className="bg-gray-50 rounded-lg p-6 border border-gray-200" suppressHydrationWarning>
            <summary className="cursor-pointer text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors">
              📐 View Detailed Patent Architecture Diagram
            </summary>
            <div className="mt-6" suppressHydrationWarning>
              <p className="text-gray-900 mb-4">
                This diagram shows our patented <strong>Context Injection Module (CIM)</strong> - highlighted in gold - which synchronously fuses physical context identifiers with sensor data at the edge. The resulting Labeled Data Objects serve operators (blue), engineers (green), and data scientists (purple).
              </p>
              <div className="bg-white p-6 rounded-lg border border-gray-300">
                {!isMounted ? (
                  <div className="text-center py-8 text-gray-500">
                    Loading diagram...
                  </div>
                ) : (
                  <div ref={diagramRef} className="mermaid"></div>
                )}
              </div>
            </div>
          </details>
        </div>
      </section>

      {/* Technology Stack */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Enterprise-Grade Technology Stack</h2>
            <p className="text-lg text-gray-700">Production-ready tools built for manufacturing reliability</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-white rounded-lg p-6 shadow-md">
              <div className="flex items-center mb-4">
                <div className="text-3xl mr-3">🖥️</div>
                <h3 className="text-xl font-bold text-gray-900">Hardware Platforms</h3>
              </div>
              <ul className="text-gray-900 space-y-3">
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">▸</span>
                  <div>
                    <strong>Edge Processing:</strong> NVIDIA Jetson Orin Nano/NX
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">▸</span>
                  <div>
                    <strong>Alternative:</strong> Smart IP cameras (Hikvision/Axis)
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">▸</span>
                  <div>
                    <strong>Cloud Infrastructure:</strong> Azure IoT Edge + Cloud
                  </div>
                </li>
              </ul>
            </div>
            <div className="bg-white rounded-lg p-6 shadow-md">
              <div className="flex items-center mb-4">
                <div className="text-3xl mr-3">⚙️</div>
                <h3 className="text-xl font-bold text-gray-900">Software Frameworks</h3>
              </div>
              <ul className="text-gray-900 space-y-3">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">▸</span>
                  <div>
                    <strong>Edge Software:</strong> Python 3.9+, OpenCV, GStreamer
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">▸</span>
                  <div>
                    <strong>Context Service:</strong> FastAPI, PostgreSQL, Redis
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">▸</span>
                  <div>
                    <strong>Data Pipeline:</strong> MinIO, Apache Arrow, AWS S3
                  </div>
                </li>
              </ul>
            </div>
            <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200">
              <div className="flex items-center mb-4">
                <div className="text-3xl mr-3">🤖</div>
                <h3 className="text-xl font-bold text-gray-900">MLOps Pipeline</h3>
              </div>
              <ul className="text-gray-900 space-y-3">
                <li className="flex items-start">
                  <span className="text-purple-500 mr-2">▸</span>
                  <div>
                    <strong>Training:</strong> PyTorch → TensorRT conversion
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="text-purple-500 mr-2">▸</span>
                  <div>
                    <strong>Deployment:</strong> Manual, Script, or K3s (50-500+ devices)
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="text-purple-500 mr-2">▸</span>
                  <div>
                    <strong>Human-in-the-Loop:</strong> Engineer approves deployments
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="text-purple-500 mr-2">▸</span>
                  <div>
                    <strong>Containers:</strong> Docker OR Podman (OT-friendly)
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Who It Serves */}
      <section className="py-16 bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Empowering Your Entire Manufacturing Team</h2>
            <p className="text-xl text-gray-700">One platform, three powerful user experiences</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            {/* Operators */}
            <div className="bg-white rounded-xl shadow-xl overflow-hidden transform hover:scale-105 transition-transform">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 text-white">
                <div className="text-6xl mb-4">👷</div>
                <h3 className="text-2xl font-bold">Operators</h3>
                <p className="text-blue-100 mt-2">Factory Floor Excellence</p>
              </div>
              <div className="p-6">
                <ul className="space-y-3 text-gray-900">
                  <li className="flex items-start">
                    <span className="text-blue-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Real-time monitoring</strong>
                      <p className="text-sm text-gray-600">See production status instantly</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Instant quality alerts</strong>
                      <p className="text-sm text-gray-600">Catch issues as they happen</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Zero data entry</strong>
                      <p className="text-sm text-gray-600">QR codes handle everything</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Perfect traceability</strong>
                      <p className="text-sm text-gray-600">Track every product and batch</p>
                    </div>
                  </li>
                </ul>
              </div>
            </div>

            {/* Engineers */}
            <div className="bg-white rounded-xl shadow-xl overflow-hidden transform hover:scale-105 transition-transform">
              <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 text-white">
                <div className="text-6xl mb-4">🔧</div>
                <h3 className="text-2xl font-bold">Engineers</h3>
                <p className="text-green-100 mt-2">Quality & Optimization</p>
              </div>
              <div className="p-6">
                <ul className="space-y-3 text-gray-900">
                  <li className="flex items-start">
                    <span className="text-green-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Immediate insights</strong>
                      <p className="text-sm text-gray-600">No more waiting for reports</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Root cause analysis</strong>
                      <p className="text-sm text-gray-600">Perfectly labeled data</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Process optimization</strong>
                      <p className="text-sm text-gray-600">Continuous improvement data</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Quality metrics</strong>
                      <p className="text-sm text-gray-600">Real-time SPC and analytics</p>
                    </div>
                  </li>
                </ul>
              </div>
            </div>

            {/* Data Scientists */}
            <div className="bg-white rounded-xl shadow-xl overflow-hidden transform hover:scale-105 transition-transform">
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 text-white">
                <div className="text-6xl mb-4">📊</div>
                <h3 className="text-2xl font-bold">Data Scientists</h3>
                <p className="text-purple-100 mt-2">ML & AI Innovation</p>
              </div>
              <div className="p-6">
                <ul className="space-y-3 text-gray-900">
                  <li className="flex items-start">
                    <span className="text-purple-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>100% accurate labels</strong>
                      <p className="text-sm text-gray-600">Ground-truth from QR codes</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Zero annotation time</strong>
                      <p className="text-sm text-gray-600">Automated labeling at source</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Ready-to-train datasets</strong>
                      <p className="text-sm text-gray-600">ML-ready from day one</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-500 text-xl mr-2">▸</span>
                    <div>
                      <strong>Pipeline integration</strong>
                      <p className="text-sm text-gray-600">Seamless data flow</p>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div className="mt-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-8 text-center">Measurable Business Impact</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg p-6 text-center shadow-lg border-t-4 border-blue-600">
                <div className="text-5xl font-bold text-blue-600 mb-2">100%</div>
                <div className="text-gray-900 font-semibold">Ground-Truth Accuracy</div>
                <p className="text-sm text-gray-600 mt-2">Physical QR codes never lie</p>
              </div>
              <div className="bg-white rounded-lg p-6 text-center shadow-lg border-t-4 border-green-600">
                <div className="text-5xl font-bold text-green-600 mb-2">{`<100`}ms</div>
                <div className="text-gray-900 font-semibold">Edge Latency</div>
                <p className="text-sm text-gray-600 mt-2">Real-time decision making</p>
              </div>
              <div className="bg-white rounded-lg p-6 text-center shadow-lg border-t-4 border-purple-600">
                <div className="text-5xl font-bold text-purple-600 mb-2">70%+</div>
                <div className="text-gray-900 font-semibold">Bandwidth Savings</div>
                <p className="text-sm text-gray-600 mt-2">Only send labeled data</p>
              </div>
              <div className="bg-white rounded-lg p-6 text-center shadow-lg border-t-4 border-orange-600">
                <div className="text-5xl font-bold text-orange-600 mb-2">90%+</div>
                <div className="text-gray-900 font-semibold">Cost Reduction</div>
                <p className="text-sm text-gray-600 mt-2">Eliminate manual annotation</p>
              </div>
            </div>
          </div>

          {/* Deployment Flexibility - NEW! */}
          <div className="mt-12 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
              Flexible Deployment for Any Factory Size
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200">
                <div className="text-4xl mb-3 text-center">🖐️</div>
                <h4 className="font-bold text-gray-900 mb-2 text-center">Manual</h4>
                <p className="text-sm text-gray-600 text-center mb-3">1-10 devices</p>
                <ul className="text-sm text-gray-700 space-y-2">
                  <li>• SSH deployment</li>
                  <li>• 15 minutes per device</li>
                  <li>• Perfect for pilots</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200">
                <div className="text-4xl mb-3 text-center">📜</div>
                <h4 className="font-bold text-gray-900 mb-2 text-center">Script</h4>
                <p className="text-sm text-gray-600 text-center mb-3">10-50 devices</p>
                <ul className="text-sm text-gray-700 space-y-2">
                  <li>• Automated bash script</li>
                  <li>• 30 minutes total</li>
                  <li>• Rollback support</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200">
                <div className="text-4xl mb-3 text-center">☸️</div>
                <h4 className="font-bold text-gray-900 mb-2 text-center">K3s</h4>
                <p className="text-sm text-gray-600 text-center mb-3">50-500+ devices</p>
                <ul className="text-sm text-gray-700 space-y-2">
                  <li>• Full automation</li>
                  <li>• 2 minutes per update</li>
                  <li>• Enterprise scale</li>
                </ul>
              </div>
            </div>
            <p className="text-center text-sm text-gray-600 mt-4">
              Docker OR Podman • Works in air-gapped environments • OT-network friendly
            </p>
          </div>
        </div>
      </section>

      {/* Implementation Roadmap */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Implementation Roadmap</h2>
            <p className="text-xl text-gray-700">Proven deployment methodology for manufacturing environments</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-lg shadow-md">
              <div className="flex items-center mb-3">
                <div className="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-bold text-lg mr-3">✓</div>
                <h3 className="text-lg font-bold text-gray-900">Phase 1</h3>
              </div>
              <p className="text-gray-900">Context Service API development</p>
              <p className="text-sm text-green-700 mt-2 font-semibold">COMPLETE</p>
            </div>

            <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-lg shadow-md">
              <div className="flex items-center mb-3">
                <div className="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-bold text-lg mr-3">✓</div>
                <h3 className="text-lg font-bold text-gray-900">Phase 2</h3>
              </div>
              <p className="text-gray-900">Edge device QR detection and basic fusion</p>
              <p className="text-sm text-green-700 mt-2 font-semibold">COMPLETE</p>
            </div>

            <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-lg shadow-md">
              <div className="flex items-center mb-3">
                <div className="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-bold text-lg mr-3">✓</div>
                <h3 className="text-lg font-bold text-gray-900">Phase 3</h3>
              </div>
              <p className="text-gray-900">LDO generation and data ingestion</p>
              <p className="text-sm text-green-700 mt-2 font-semibold">COMPLETE</p>
            </div>

            <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded-lg shadow-md">
              <div className="flex items-center mb-3">
                <div className="w-10 h-10 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold text-lg mr-3">4</div>
                <h3 className="text-lg font-bold text-gray-900">Phase 4</h3>
              </div>
              <p className="text-gray-900">Integration testing in lab environment</p>
              <p className="text-sm text-blue-700 mt-2 font-semibold">IN PROGRESS</p>
            </div>

            <div className="bg-gray-50 border-l-4 border-gray-400 p-6 rounded-lg shadow-md">
              <div className="flex items-center mb-3">
                <div className="w-10 h-10 bg-gray-400 text-white rounded-full flex items-center justify-center font-bold text-lg mr-3">5</div>
                <h3 className="text-lg font-bold text-gray-900">Phase 5</h3>
              </div>
              <p className="text-gray-900">Factory pilot deployment</p>
              <p className="text-sm text-gray-600 mt-2 font-semibold">PLANNED</p>
            </div>

            <div className="bg-gray-50 border-l-4 border-gray-400 p-6 rounded-lg shadow-md">
              <div className="flex items-center mb-3">
                <div className="w-10 h-10 bg-gray-400 text-white rounded-full flex items-center justify-center font-bold text-lg mr-3">6</div>
                <h3 className="text-lg font-bold text-gray-900">Phase 6</h3>
              </div>
              <p className="text-gray-900">Production scaling and monitoring</p>
              <p className="text-sm text-gray-600 mt-2 font-semibold">PLANNED</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gradient-to-br from-gray-800 to-gray-900 text-white py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center border-b border-gray-700 pb-6 mb-6">
            <h3 className="text-2xl font-bold mb-2">Context Edge</h3>
            <p className="text-gray-400">Patented Context Injection Module (CIM) Technology</p>
          </div>
          <div className="text-center">
            <p className="mb-2 text-gray-300">Empowering Operators, Engineers & Data Scientists in Manufacturing</p>
            <p className="text-sm text-gray-500">&copy; 2025 Context Edge. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
