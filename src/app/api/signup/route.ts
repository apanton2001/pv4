import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { name, email } = body;
    
    // Here you would typically:
    // 1. Validate the email
    // 2. Store in database
    // 3. Send confirmation email
    // 4. Log the signup
    
    console.log(`New signup: ${name} (${email})`);
    
    // For now, just return success
    return NextResponse.json(
      { success: true, message: 'Thank you for signing up for the beta!' },
      { status: 200 }
    );
  } catch (error) {
    console.error('Signup error:', error);
    return NextResponse.json(
      { success: false, message: 'Something went wrong' },
      { status: 500 }
    );
  }
} 