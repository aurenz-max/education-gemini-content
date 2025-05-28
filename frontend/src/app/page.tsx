// app/page.tsx - Simplified version
'use client';

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight mb-4">
            Educational Content Review System
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            AI-powered educational content generation with comprehensive review tools
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
            <h2 className="text-xl font-semibold mb-2">Content Library</h2>
            <p className="text-gray-600 mb-4">
              Browse and manage all generated content packages
            </p>
            <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              View Library
            </button>
          </div>

          <div className="border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
            <h2 className="text-xl font-semibold mb-2">Generate Content</h2>
            <p className="text-gray-600 mb-4">
              Create new educational content packages
            </p>
            <button className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
              Generate New
            </button>
          </div>
        </div>

        <div className="border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">What We Generate</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl mb-2">📄</div>
              <h3 className="font-medium">Reading Content</h3>
              <p className="text-sm text-gray-600">Structured explanatory text</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl mb-2">👁️</div>
              <h3 className="font-medium">Visual Demo</h3>
              <p className="text-sm text-gray-600">Interactive demonstrations</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl mb-2">🔊</div>
              <h3 className="font-medium">Audio Content</h3>
              <p className="text-sm text-gray-600">Teacher-student dialogue</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl mb-2">📝</div>
              <h3 className="font-medium">Practice Problems</h3>
              <p className="text-sm text-gray-600">Assessment questions</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}