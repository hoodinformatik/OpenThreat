export default function PrivacyPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">Privacy Policy</h1>

      <div className="prose prose-lg max-w-none space-y-8">
        {/* Responsible Party */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Responsible Party</h2>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
            This website is operated privately and without commercial purposes.
          </p>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-2">
            Responsible for data processing: <a href="mailto:hoodinformatik@gmail.com" className="text-blue-600 dark:text-blue-400 hover:underline">hoodinformatik@gmail.com</a>
          </p>
        </section>

        {/* General Information */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">General Information on Data Processing</h2>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
            When you visit this website, technical data is automatically processed that your browser transmits to the server
            (e.g., IP address, browser type, date and time of access). This data is necessary to display the website and
            ensure its security.
          </p>
        </section>

        {/* Cloudflare */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Use of Cloudflare</h2>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
            To secure and optimize the delivery of this website, we use the service Cloudflare
            (Provider: Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, USA).
          </p>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
            Cloudflare may process technical data (e.g., IP addresses) to defend against attacks and improve performance.
          </p>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
            The data processing is based on Art. 6 para. 1 lit. f GDPR (legitimate interest in secure and efficient
            operation of this website).
          </p>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
            Cloudflare acts as a data processor in accordance with Art. 28 GDPR; a corresponding agreement exists.
          </p>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
            For more information, please visit:{" "}
            <a
              href="https://www.cloudflare.com/privacypolicy/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              https://www.cloudflare.com/privacypolicy/
            </a>
          </p>
        </section>

        {/* Cookies */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Cookies</h2>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
            This website does not use cookies that require consent (e.g., tracking or marketing cookies).
          </p>
        </section>

        {/* Rights */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Rights of Data Subjects</h2>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
            You have the right to access, rectification, deletion, and restriction of processing of your personal data,
            as well as the right to lodge a complaint with a supervisory authority.
          </p>
        </section>

        {/* Last Updated */}
        <section className="pt-8 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Last updated: October 21, 2025
          </p>
        </section>
      </div>
    </div>
  );
}
