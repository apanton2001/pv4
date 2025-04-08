import { NextRequest, NextResponse } from 'next/server';

/**
 * This is a secure proxy to your trading bot API.
 * It handles authentication and forwards requests to your backend API.
 */

// Helper to check if the user is authenticated
// In a real app, this would check against your auth system (Supabase, etc.)
async function isAuthenticated(request: NextRequest): Promise<boolean> {
  // In a production environment, you would validate the user's session here
  // For example, with Supabase Auth:
  // const supabase = createServerSupabaseClient();
  // const { data: { user }, error } = await supabase.auth.getUser();
  // return !!user && !error;
  
  // For development, we'll just return true
  return true;
}

// Helper to check if the user has an active subscription
// In a real app, this would check against your subscription system
async function hasActiveSubscription(userId: string): Promise<boolean> {
  // In a production environment, you would check the user's subscription status
  // For example, with a database query or Stripe API call
  
  // For development, we'll just return true
  return true;
}

export async function POST(request: NextRequest) {
  try {
    // Check if the user is authenticated
    const isUserAuthenticated = await isAuthenticated(request);
    if (!isUserAuthenticated) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Extract the endpoint from the URL
    // e.g., /api/cursor-ai-proxy/generate-signals -> /generate-signals
    const url = new URL(request.url);
    const endpoint = url.pathname.replace('/api/cursor-ai-proxy', '');
    
    // For subscription-gated features, check subscription
    if (['/portfolio-optimization', '/execute-trade'].includes(endpoint)) {
      // In a real app, you would get the user ID from the session
      const userId = 'mock-user-id'; 
      const hasSubscription = await hasActiveSubscription(userId);
      
      if (!hasSubscription) {
        return NextResponse.json(
          { error: 'Subscription required' },
          { status: 403 }
        );
      }
    }
    
    // Forward the request to your trading bot API
    const apiUrl = `${process.env.CURSOR_AI_API_URL}${endpoint}`;
    const apiKey = process.env.CURSOR_AI_API_KEY;
    
    if (!apiUrl || !apiKey) {
      console.error('Missing API URL or API Key');
      return NextResponse.json(
        { error: 'Server configuration error' },
        { status: 500 }
      );
    }
    
    // Get the request body
    const body = await request.json();
    
    // Forward the request with the API key in the headers
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    });
    
    // Return the response from the API
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
    
  } catch (error) {
    console.error('Error in cursor-ai-proxy:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    // Check if the user is authenticated
    const isUserAuthenticated = await isAuthenticated(request);
    if (!isUserAuthenticated) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Extract the endpoint from the URL
    const url = new URL(request.url);
    const endpoint = url.pathname.replace('/api/cursor-ai-proxy', '');
    
    // Forward the request to your trading bot API
    const apiUrl = `${process.env.CURSOR_AI_API_URL}${endpoint}`;
    const apiKey = process.env.CURSOR_AI_API_KEY;
    
    if (!apiUrl || !apiKey) {
      console.error('Missing API URL or API Key');
      return NextResponse.json(
        { error: 'Server configuration error' },
        { status: 500 }
      );
    }
    
    // Forward the request with the API key in the headers
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
    });
    
    // Return the response from the API
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
    
  } catch (error) {
    console.error('Error in cursor-ai-proxy:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 