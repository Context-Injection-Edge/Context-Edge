'use client';

import { useState, useEffect } from 'react';

interface FeedbackItem {
  sensor_data: Record<string, any>;
  prediction: {
    failure_mode: string;
    confidence: number;
    timestamp: number;
  };
  cid: string;
  timestamp: number;
  needs_retraining: boolean;
}

export default function FeedbackPage() {
  const [feedbackItems, setFeedbackItems] = useState<FeedbackItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<FeedbackItem | null>(null);
  const [validation, setValidation] = useState<'correct' | 'incorrect' | ''>('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchFeedback();
  }, []);

  const fetchFeedback = async () => {
    setLoading(true);
    try {
      // Mock data for now - in real implementation, call /feedback/batch
      const mockFeedback: FeedbackItem[] = [
        {
          sensor_data: {
            vibration_x: 1.2,
            vibration_y: 0.8,
            temperature: 75,
            current: 9.5,
            timestamp: Date.now() - 3600000
          },
          prediction: {
            failure_mode: 'Bearing Wear',
            confidence: 0.65,
            timestamp: Date.now() - 3600000
          },
          cid: 'QR-Bearing-001',
          timestamp: Date.now() - 3600000,
          needs_retraining: true
        },
        {
          sensor_data: {
            vibration_x: 0.9,
            vibration_y: 1.1,
            temperature: 82,
            current: 11.2,
            timestamp: Date.now() - 7200000
          },
          prediction: {
            failure_mode: 'Belt Slippage',
            confidence: 0.58,
            timestamp: Date.now() - 7200000
          },
          cid: 'QR-Belt-002',
          timestamp: Date.now() - 7200000,
          needs_retraining: true
        },
        {
          sensor_data: {
            vibration_x: 2.1,
            vibration_y: 1.8,
            temperature: 95,
            current: 13.8,
            timestamp: Date.now() - 10800000
          },
          prediction: {
            failure_mode: 'Motor Overload',
            confidence: 0.72,
            timestamp: Date.now() - 10800000
          },
          cid: 'QR-Motor-003',
          timestamp: Date.now() - 10800000,
          needs_retraining: true
        }
      ];
      setFeedbackItems(mockFeedback);
    } catch (error) {
      console.error('Error fetching feedback:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitValidation = async () => {
    if (!selectedItem || !validation) return;

    try {
      // In real implementation, submit to retraining pipeline
      const feedbackData = {
        original_prediction: selectedItem.prediction,
        validation: validation,
        notes: notes,
        validated_by: 'engineer', // In real app, get from auth
        validated_at: Date.now()
      };

      // Mock API call
      console.log('Submitting validation:', feedbackData);

      // Remove from queue
      setFeedbackItems(feedbackItems.filter(item =>
        item.timestamp !== selectedItem.timestamp
      ));

      // Reset form
      setSelectedItem(null);
      setValidation('');
      setNotes('');

      alert('Validation submitted for retraining');

    } catch (error) {
      console.error('Error submitting validation:', error);
      alert('Error submitting validation');
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence < 0.6) return 'text-red-600 bg-red-50';
    if (confidence < 0.8) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Feedback Queue</h1>
          <div className="flex gap-2">
            <button
              onClick={fetchFeedback}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Refresh Queue
            </button>
            <a
              href="/admin"
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Back to Admin
            </a>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8">Loading feedback queue...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Feedback Queue */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">
                  Low-Confidence Predictions ({feedbackItems.length})
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  Predictions requiring human validation for model retraining
                </p>
              </div>
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {feedbackItems.map((item) => (
                  <div
                    key={item.timestamp}
                    className={`p-4 cursor-pointer hover:bg-gray-50 ${
                      selectedItem?.timestamp === item.timestamp ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                    onClick={() => setSelectedItem(item)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{item.prediction.failure_mode}</h3>
                        <p className="text-sm text-gray-600">CID: {item.cid}</p>
                      </div>
                      <div className={`px-2 py-1 rounded text-sm font-semibold ${getConfidenceColor(item.prediction.confidence)}`}>
                        {(item.prediction.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(item.timestamp).toLocaleString()}
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                      <div>Vib X: {item.sensor_data.vibration_x}g</div>
                      <div>Temp: {item.sensor_data.temperature}°C</div>
                      <div>Vib Y: {item.sensor_data.vibration_y}g</div>
                      <div>Current: {item.sensor_data.current}A</div>
                    </div>
                  </div>
                ))}
                {feedbackItems.length === 0 && (
                  <div className="p-6 text-center text-gray-700">
                    No items in feedback queue. All predictions are confident!
                  </div>
                )}
              </div>
            </div>

            {/* Validation Panel */}
            <div className="bg-white rounded-lg shadow-md p-6">
              {selectedItem ? (
                <>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    Validate Prediction
                  </h2>

                  <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-semibold mb-2">Prediction Details</h3>
                    <div className="space-y-2 text-sm">
                      <div><strong>Failure Mode:</strong> {selectedItem.prediction.failure_mode}</div>
                      <div><strong>Confidence:</strong> {(selectedItem.prediction.confidence * 100).toFixed(1)}%</div>
                      <div><strong>Context ID:</strong> {selectedItem.cid}</div>
                      <div><strong>Timestamp:</strong> {new Date(selectedItem.timestamp).toLocaleString()}</div>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className="font-semibold mb-2">Sensor Data</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="p-3 bg-blue-50 rounded">
                        <div className="font-medium">Vibration X</div>
                        <div className="text-lg">{selectedItem.sensor_data.vibration_x} g</div>
                      </div>
                      <div className="p-3 bg-blue-50 rounded">
                        <div className="font-medium">Vibration Y</div>
                        <div className="text-lg">{selectedItem.sensor_data.vibration_y} g</div>
                      </div>
                      <div className="p-3 bg-red-50 rounded">
                        <div className="font-medium">Temperature</div>
                        <div className="text-lg">{selectedItem.sensor_data.temperature} °C</div>
                      </div>
                      <div className="p-3 bg-green-50 rounded">
                        <div className="font-medium">Current</div>
                        <div className="text-lg">{selectedItem.sensor_data.current} A</div>
                      </div>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className="font-semibold mb-3">Validation</h3>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="validation"
                          value="correct"
                          checked={validation === 'correct'}
                          onChange={(e) => setValidation(e.target.value as 'correct')}
                          className="mr-2"
                        />
                        <span className="text-green-700 font-medium">Correct - This prediction is accurate</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="validation"
                          value="incorrect"
                          checked={validation === 'incorrect'}
                          onChange={(e) => setValidation(e.target.value as 'incorrect')}
                          className="mr-2"
                        />
                        <span className="text-red-700 font-medium">Incorrect - This is a false positive</span>
                      </label>
                    </div>
                  </div>

                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-900 mb-2">
                      Notes (Optional)
                    </label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Add any observations or corrective actions..."
                    />
                  </div>

                  <button
                    onClick={submitValidation}
                    disabled={!validation}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Submit for Retraining
                  </button>
                </>
              ) : (
                <div className="text-center text-gray-700 py-8">
                  Select a feedback item to validate
                </div>
              )}
            </div>
          </div>
        )}

        {/* Queue Statistics */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Queue Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {feedbackItems.length}
              </div>
              <div className="text-gray-600">Items in Queue</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600 mb-2">
                {feedbackItems.filter(item => item.prediction.confidence < 0.6).length}
              </div>
              <div className="text-gray-600">High Priority (&lt;60%)</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600 mb-2">
                {feedbackItems.filter(item => item.prediction.confidence >= 0.6 && item.prediction.confidence < 0.8).length}
              </div>
              <div className="text-gray-600">Medium Priority (60-80%)</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {feedbackItems.filter(item => item.prediction.confidence >= 0.8).length}
              </div>
              <div className="text-gray-600">Low Priority (&ge;80%)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}