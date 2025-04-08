/**
 * Cursor AI API Client
 * 
 * This client handles communication with the Prometheus Trading Bot API.
 */

type ApiResponse<T> = {
  success: boolean;
  data?: T;
  error?: string;
};

type SignalData = {
  pair: string;
  direction: 'buy' | 'sell';
  confidence: number;
  timestamp: string;
  indicators?: Record<string, any>;
};

type MarketAnalysisData = {
  timestamp: string;
  volatility: Record<string, any>;
  trends: Record<string, any>;
  marketSummary: {
    regime: string;
    averageVolatility: number;
    trendStrength: number;
    riskScore: number;
  };
};

type PortfolioData = {
  assets: Array<{
    id: string;
    symbol: string;
    allocation: number;
    value: number;
  }>;
  totalValue: number;
  lastUpdated: string;
};

export class CursorAiClient {
  private apiUrl: string;
  
  constructor() {
    // Use the public URL for client-side requests
    this.apiUrl = process.env.NEXT_PUBLIC_CURSOR_AI_API_URL || '/api/cursor-ai-proxy';
  }
  
  /**
   * Generate trading signals based on the given parameters
   */
  async generateSignals(timeframe: string, pairs: string[], strategyParams: Record<string, any>): Promise<ApiResponse<SignalData[]>> {
    try {
      const response = await fetch(`${this.apiUrl}/generate-signals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          timeframe,
          pairs,
          strategyParams,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        return { success: false, error: errorData.error || 'Failed to generate signals' };
      }
      
      const data = await response.json();
      return { success: true, data: data.signals };
    } catch (error) {
      console.error('Error generating signals:', error);
      return { success: false, error: 'An error occurred while generating signals' };
    }
  }
  
  /**
   * Analyze market conditions for the specified markets
   */
  async analyzeMarket(markets: string[], timeframe: string, lookbackDays: number): Promise<ApiResponse<MarketAnalysisData>> {
    try {
      const response = await fetch(`${this.apiUrl}/market-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          markets,
          timeframe,
          lookbackDays,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        return { success: false, error: errorData.error || 'Failed to analyze market' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('Error analyzing market:', error);
      return { success: false, error: 'An error occurred while analyzing market' };
    }
  }
  
  /**
   * Optimize portfolio based on user preferences
   */
  async optimizePortfolio(userId: string, riskTolerance: number, investmentHorizon: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.apiUrl}/portfolio-optimization`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId,
          riskTolerance,
          investmentHorizon,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        return { success: false, error: errorData.error || 'Failed to optimize portfolio' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('Error optimizing portfolio:', error);
      return { success: false, error: 'An error occurred while optimizing portfolio' };
    }
  }
  
  /**
   * Execute a trade
   */
  async executeTrade(userId: string, apiKey: string, trade: {
    exchange: string;
    symbol: string;
    type: string;
    side: 'buy' | 'sell';
    amount: number;
    price?: number;
  }): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.apiUrl}/execute-trade`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId,
          apiKey,
          trade,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        return { success: false, error: errorData.error || 'Failed to execute trade' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('Error executing trade:', error);
      return { success: false, error: 'An error occurred while executing trade' };
    }
  }
  
  /**
   * Get user portfolio data
   */
  async getUserPortfolio(userId: string): Promise<ApiResponse<PortfolioData>> {
    try {
      const response = await fetch(`${this.apiUrl}/portfolio/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        return { success: false, error: errorData.error || 'Failed to get portfolio' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('Error getting portfolio:', error);
      return { success: false, error: 'An error occurred while getting portfolio' };
    }
  }
}

// Export a singleton instance
export const cursorAiClient = new CursorAiClient(); 