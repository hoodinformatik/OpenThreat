'use client';

import { useState, useEffect } from 'react';
import { Shield, Mail, CheckCircle, Rocket, Users, Lock } from 'lucide-react';

export default function WaitlistPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [waitlistCount, setWaitlistCount] = useState<number | null>(null);

  // Fetch waitlist count
  useEffect(() => {
    fetchWaitlistCount();
  }, []);

  const fetchWaitlistCount = async () => {
    try {
      const response = await fetch('/api/v1/waitlist/count');
      const data = await response.json();
      setWaitlistCount(data.count);
    } catch (err) {
      console.error('Failed to fetch waitlist count:', err);
    }
  };

  const handleJoinWaitlist = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/v1/waitlist/join', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to join waitlist');
      }

      if (data.already_verified) {
        setError('✅ This email is already on the waitlist!');
      } else {
        setSuccess(true);
        setEmail('');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to join waitlist');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="bg-blue-600 p-4 rounded-2xl shadow-lg">
              <Shield className="h-16 w-16 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
            OpenThreat
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-2">
            Democratizing Threat Intelligence
          </p>
          <div className="inline-flex items-center px-4 py-2 bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-full">
            <Rocket className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2" />
            <span className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
              Currently in Beta Phase
            </span>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {/* Beta Notice */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 mb-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                🚧 We're Building Something Special
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-300">
                OpenThreat is currently in private beta. Join our waitlist and we'll notify you when we launch!
              </p>
            </div>

            {/* Features Grid */}
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="text-center p-6 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                <Shield className="h-12 w-12 text-blue-600 dark:text-blue-400 mx-auto mb-3" />
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Real-time CVE Tracking
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Stay updated with the latest vulnerabilities from CISA, NVD, and more
                </p>
              </div>

              <div className="text-center p-6 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
                <Lock className="h-12 w-12 text-purple-600 dark:text-purple-400 mx-auto mb-3" />
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Privacy-First
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  No tracking, no analytics, your data stays yours
                </p>
              </div>

              <div className="text-center p-6 bg-green-50 dark:bg-green-900/20 rounded-xl">
                <Users className="h-12 w-12 text-green-600 dark:text-green-400 mx-auto mb-3" />
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Community-Driven
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Open source and built for the security community
                </p>
              </div>
            </div>

            {/* Waitlist Form */}
            {!success ? (
              <form onSubmit={handleJoinWaitlist} className="max-w-md mx-auto">
                <div className="mb-6">
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Join the Waitlist
                  </label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        id="email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="your@email.com"
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                    >
                      {loading ? 'Joining...' : 'Join Waitlist'}
                    </button>
                  </div>
                  {waitlistCount !== null && (
                    <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 text-center">
                      🎉 {waitlistCount} security professionals already joined
                    </p>
                  )}
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
                    We'll send you a verification link to confirm your email
                  </p>
                </div>

                {error && (
                  <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4">
                    <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                  </div>
                )}
              </form>
            ) : (
              <div className="max-w-md mx-auto text-center">
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
                  <CheckCircle className="h-16 w-16 text-green-600 dark:text-green-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    📧 Check Your Email!
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300 mb-4">
                    We've sent you a verification link. Please click the link in your email to confirm your signup.
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Didn't receive it? Check your spam folder or try again.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Why OpenThreat */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">
              Why OpenThreat?
            </h2>
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <span className="text-blue-600 dark:text-blue-400 font-bold text-sm">✓</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white">Centralized Intelligence</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    All major vulnerability sources in one place - CISA KEV, NVD, and more
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <span className="text-blue-600 dark:text-blue-400 font-bold text-sm">✓</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white">AI-Powered Analysis</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Automated threat analysis and MITRE ATT&CK mapping with LLM technology
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <span className="text-blue-600 dark:text-blue-400 font-bold text-sm">✓</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white">Community Features</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Collaborate with security professionals, share insights, and vote on critical vulnerabilities
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <span className="text-blue-600 dark:text-blue-400 font-bold text-sm">✓</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white">100% Open Source</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Transparent, auditable, and free forever. Check us out on GitHub!
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center mt-8 text-sm text-gray-500 dark:text-gray-400">
            <p>Built with ❤️ by the security community</p>
            <p className="mt-2">
              <a
                href="https://github.com/hoodinformatik/OpenThreat"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                View on GitHub
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
