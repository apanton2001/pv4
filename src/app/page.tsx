import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-primary-900 to-primary-950">
      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center text-white">
          <h1 className="text-5xl font-bold mb-6">Prometheus Bot</h1>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Sophisticated algorithmic trading with 66.7% win rate and minimal drawdown
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link 
              href="#signup"
              className="bg-secondary-500 hover:bg-secondary-600 px-6 py-3 rounded-md font-medium text-white"
            >
              Join Beta
            </Link>
            <Link 
              href="#features"
              className="border border-white hover:bg-white/10 px-6 py-3 rounded-md font-medium text-white"
            >
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-16 px-4 bg-white">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-primary-800">Advanced Trading Features</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-primary-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-3 text-primary-700">Multi-Timeframe Analysis</h3>
              <p className="text-gray-700">Sophisticated analysis across multiple timeframes (5m, 15m, 1h, 4h) for precise entry and exit points.</p>
            </div>
            
            <div className="bg-primary-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-3 text-primary-700">Advanced Risk Management</h3>
              <p className="text-gray-700">Dynamic position sizing based on volatility with strict drawdown protection.</p>
            </div>
            
            <div className="bg-primary-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-3 text-primary-700">Market Regime Detection</h3>
              <p className="text-gray-700">Adaptive trading parameters based on current market conditions (bullish, bearish, ranging).</p>
            </div>
          </div>
        </div>
      </section>

      {/* Performance Stats */}
      <section className="py-16 px-4 bg-primary-800 text-white">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Proven Performance</h2>
          
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <p className="text-4xl font-bold text-secondary-400">66.7%</p>
              <p className="mt-2">Win Rate</p>
            </div>
            
            <div>
              <p className="text-4xl font-bold text-secondary-400">-0.17%</p>
              <p className="mt-2">Maximum Drawdown</p>
            </div>
            
            <div>
              <p className="text-4xl font-bold text-secondary-400">3-5%</p>
              <p className="mt-2">Weekly ROI Target</p>
            </div>
          </div>
        </div>
      </section>

      {/* Beta Signup */}
      <section id="signup" className="py-16 px-4 bg-white">
        <div className="container mx-auto max-w-md">
          <div className="bg-primary-50 p-8 rounded-lg shadow-lg">
            <h3 className="text-2xl font-semibold mb-6 text-primary-800 text-center">Join the Beta</h3>
            <form className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input 
                  type="text" 
                  id="name" 
                  className="w-full p-3 border border-gray-300 rounded-md" 
                  placeholder="Your name"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input 
                  type="email" 
                  id="email" 
                  className="w-full p-3 border border-gray-300 rounded-md" 
                  placeholder="Your email"
                  required
                />
              </div>
              
              <button 
                type="submit"
                className="w-full bg-primary-600 text-white py-3 rounded-md hover:bg-primary-700 font-medium"
              >
                Get Early Access
              </button>
              
              <p className="text-xs text-center text-gray-500 mt-4">
                Join our limited beta release. Early access includes 50% discount for first 100 users.
              </p>
            </form>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-primary-950 text-white py-8 px-4">
        <div className="container mx-auto text-center">
          <p>&copy; 2025 Prometheus Bot. All rights reserved.</p>
        </div>
      </footer>
    </main>
  )
} 