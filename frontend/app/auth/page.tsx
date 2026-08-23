import { Shield, Clock } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function AuthPage() {
  return (
    <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-primary p-3 rounded-2xl">
              <Shield className="h-10 w-10 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">OpenThreat</h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <Clock className="h-5 w-5" />
              <span>Accounts Coming Soon</span>
            </CardTitle>
            <CardDescription>
              Sign-in isn&apos;t available yet
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Voting, comments, bookmarks and notifications require an account,
              which we&apos;re not offering yet. All CVE data, search, and the RSS
              feeds are fully available without one.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
