'use client';

import { useState } from 'react';
import { cursorAiClient } from '../lib/cursor-ai-client';

export default function Home() {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Function to generate trading signals
  async function handleGenerateSignals() {
    setLoading(true);
    setError(null);

    try {
      const { success, data, error: apiError } = await cursorAiClient.generateSignals(
        '1h',
        ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
        {
          fastPeriod: 8,
          slowPeriod: 21,
          rsiPeriod: 14,
          rsiOverbought: 70,
          rsiOversold: 30
        }
      );

      if (!success) {
        throw new Error(apiError || 'Failed to generate signals');
      }

      setSignals(data || []);
    } catch (err: any) {
      console.error('Error generating signals:', err);
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Prometheus Trading Bot</h1>
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Trading Signals</h2>
          
          <button
            onClick={handleGenerateSignals}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Generate Signals'}
          </button>
          
          {error && (
            <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md">
              Error: {error}
            </div>
          )}
          
          {signals.length > 0 ? (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {signals.map((signal, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <h3 className="font-bold text-lg">{signal.pair}</h3>
                  <p className={`font-medium ${signal.direction === 'buy' ? 'text-green-600' : 'text-red-600'}`}>
                    {signal.direction.toUpperCase()}
                  </p>
                  <p className="text-sm text-gray-600">
                    Confidence: {(signal.confidence * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(signal.timestamp).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-gray-600">
              No signals generated yet. Click the button above to generate trading signals.
            </p>
          )}
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Integration Information</h2>
          <p className="mb-3">
            This demo shows how the v0 functions integration works with your trading bot.
          </p>
          <p className="mb-3">
            The frontend makes requests to the secure proxy at <code>/api/cursor-ai-proxy</code>,
            which then securely forwards them to your trading bot API.
          </p>
          <p>
            This architecture ensures that your API keys remain secure and allows for 
            subscription-based access control.
          </p>
        </div>
      </div>
    </div>
  );
} 