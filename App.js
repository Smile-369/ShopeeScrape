import React, { useState, useEffect } from 'react';
import { Search, Store, MessageSquare, BarChart3, Play, Download, AlertCircle, CheckCircle, Loader2, Info, Power, Wifi, WifiOff } from 'lucide-react';

const API_URL = 'http://localhost:5000';

const ShopeeScraperUI = () => {
  const [activeTab, setActiveTab] = useState('search');
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState(null);
  const [logs, setLogs] = useState([]);
  const [connected, setConnected] = useState(false);
  const [driverInitialized, setDriverInitialized] = useState(false);
  const [taskId, setTaskId] = useState(null);

  // Form states
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchPages, setSearchPages] = useState(10);
  const [shopId, setShopId] = useState('');
  const [includeActive, setIncludeActive] = useState(true);
  const [includeSoldOut, setIncludeSoldOut] = useState(true);
  const [reviewsFile, setReviewsFile] = useState(null);
  const [maxReviews, setMaxReviews] = useState(1000);
  const [analyzeFile, setAnalyzeFile] = useState(null);

  useEffect(() => {
    // Check server health on mount
    checkHealth();
    
    // Poll server health every 5 seconds
    const healthInterval = setInterval(checkHealth, 5000);
    
    return () => clearInterval(healthInterval);
  }, []);

  // Poll for task status when a task is running
  useEffect(() => {
    if (!isRunning) return;
    
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/task-status/${taskId}`);
        const data = await response.json();
        
        if (data.logs && data.logs.length > 0) {
          data.logs.forEach(log => {
            addLog(log.message, log.type);
          });
        }
        
        if (data.status === 'completed') {
          setIsRunning(false);
          if (data.result) {
            setResults(data.result);
          }
          addLog('Task completed successfully!', 'success');
        } else if (data.status === 'error') {
          setIsRunning(false);
          addLog(`Error: ${data.error}`, 'error');
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);
    
    return () => clearInterval(pollInterval);
  }, [isRunning, taskId]);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`);
      const data = await response.json();
      setConnected(true);
      setDriverInitialized(data.driver_initialized);
    } catch (error) {
      setConnected(false);
      console.error('Health check failed:', error);
    }
  };

  const addLog = (message, type = 'info') => {
    setLogs(prev => {
      // Avoid duplicate consecutive logs
      if (prev.length > 0 && prev[prev.length - 1].message === message) {
        return prev;
      }
      return [...prev, { message, type, time: new Date().toLocaleTimeString() }];
    });
  };

  const initializeDriver = async () => {
    try {
      addLog('Initializing driver...', 'info');
      const response = await fetch(`${API_URL}/api/initialize-driver`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        setDriverInitialized(true);
        addLog(data.message, 'success');
      } else {
        addLog(data.error, 'error');
      }
    } catch (error) {
      addLog(`Error: ${error.message}`, 'error');
    }
  };

  const handleSearch = async () => {
    setIsRunning(true);
    setResults(null);
    setLogs([]);
    
    try {
      const response = await fetch(`${API_URL}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyword: searchKeyword,
          pages: searchPages
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setTaskId(data.task_id);
        addLog('Search task started...', 'info');
      } else {
        addLog(data.error, 'error');
        setIsRunning(false);
      }
    } catch (error) {
      addLog(`Error: ${error.message}`, 'error');
      setIsRunning(false);
    }
  };

  const handleShopScrape = async () => {
    setIsRunning(true);
    setResults(null);
    setLogs([]);
    
    try {
      const response = await fetch(`${API_URL}/api/shop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          shop_id: shopId,
          include_active: includeActive,
          include_soldout: includeSoldOut
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setTaskId(data.task_id);
        addLog('Shop scraping task started...', 'info');
      } else {
        addLog(data.error, 'error');
        setIsRunning(false);
      }
    } catch (error) {
      addLog(`Error: ${error.message}`, 'error');
      setIsRunning(false);
    }
  };

  const handleReviewsScrape = async () => {
    if (!reviewsFile) return;
    
    setIsRunning(true);
    setResults(null);
    setLogs([]);
    
    const formData = new FormData();
    formData.append('file', reviewsFile);
    formData.append('max_reviews', maxReviews);
    
    try {
      const response = await fetch(`${API_URL}/api/reviews`, {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      if (data.success) {
        setTaskId(data.task_id);
        addLog('Review scraping task started...', 'info');
      } else {
        addLog(data.error, 'error');
        setIsRunning(false);
      }
    } catch (error) {
      addLog(`Error: ${error.message}`, 'error');
      setIsRunning(false);
    }
  };

  const handleAnalyze = async () => {
    if (!analyzeFile) return;
    
    setIsRunning(true);
    setResults(null);
    setLogs([]);
    
    const formData = new FormData();
    formData.append('file', analyzeFile);
    
    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      if (data.success) {
        setTaskId(data.task_id);
        addLog('Analysis task started...', 'info');
      } else {
        addLog(data.error, 'error');
        setIsRunning(false);
      }
    } catch (error) {
      addLog(`Error: ${error.message}`, 'error');
      setIsRunning(false);
    }
  };

  const downloadFile = (filename) => {
    window.open(`${API_URL}/api/download/${filename}`, '_blank');
  };

  const TabButton = ({ id, icon: Icon, label }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`flex items-center gap-2 px-6 py-3 font-medium transition-all ${
        activeTab === id
          ? 'bg-orange-500 text-white shadow-lg'
          : 'bg-white text-gray-700 hover:bg-gray-50'
      } rounded-lg`}
    >
      <Icon size={20} />
      {label}
    </button>
  );

  const LogEntry = ({ message, type, time }) => (
    <div className={`flex items-start gap-3 p-3 rounded-lg ${
      type === 'success' ? 'bg-green-50 text-green-800' :
      type === 'error' ? 'bg-red-50 text-red-800' :
      'bg-blue-50 text-blue-800'
    }`}>
      {type === 'success' && <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />}
      {type === 'error' && <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />}
      {type === 'info' && <Info size={16} className="mt-0.5 flex-shrink-0" />}
      <div className="flex-1">
        <p className="text-sm font-medium">{message}</p>
        <p className="text-xs opacity-70 mt-0.5">{time}</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-red-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-8 shadow-xl">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">Shopee Scraper & Analyzer</h1>
              <p className="text-orange-100">Extract product data, reviews, and perform sentiment analysis</p>
            </div>
            <div className="flex gap-3">
              <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                connected ? 'bg-green-500' : 'bg-red-500'
              }`}>
                {connected ? <Wifi size={20} /> : <WifiOff size={20} />}
                <span className="text-sm font-medium">
                  {connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              {!driverInitialized && (
                <button
                  onClick={initializeDriver}
                  className="flex items-center gap-2 px-4 py-2 bg-white text-orange-600 rounded-lg font-medium hover:bg-orange-50 transition-colors"
                >
                  <Power size={20} />
                  Initialize Driver
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        {/* Warning if driver not initialized */}
        {!driverInitialized && (
          <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
            <div className="flex items-center gap-3">
              <AlertCircle className="text-yellow-600" size={24} />
              <div>
                <p className="font-medium text-yellow-800">Driver Not Initialized</p>
                <p className="text-sm text-yellow-700">Click "Initialize Driver" and login to Shopee before scraping</p>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-3 mb-6 flex-wrap">
          <TabButton id="search" icon={Search} label="Search Products" />
          <TabButton id="shop" icon={Store} label="Shop Items" />
          <TabButton id="reviews" icon={MessageSquare} label="Reviews" />
          <TabButton id="analyze" icon={BarChart3} label="Analyze" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-lg p-6">
            {/* Search Tab */}
            {activeTab === 'search' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Search Products</h2>
                <p className="text-gray-600 mb-6">Search for products by keyword and scrape results</p>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Search Keyword *
                    </label>
                    <input
                      type="text"
                      value={searchKeyword}
                      onChange={(e) => setSearchKeyword(e.target.value)}
                      placeholder="e.g., laptop, phone, headphones"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Number of Pages
                    </label>
                    <input
                      type="number"
                      value={searchPages}
                      onChange={(e) => setSearchPages(Number(e.target.value))}
                      min="1"
                      max="50"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">Each page contains ~60 items</p>
                  </div>

                  <button
                    onClick={handleSearch}
                    disabled={isRunning || !searchKeyword || !driverInitialized}
                    className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-3 px-6 rounded-lg font-semibold hover:from-orange-600 hover:to-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isRunning ? <Loader2 className="animate-spin" size={20} /> : <Play size={20} />}
                    {isRunning ? 'Scraping...' : 'Start Scraping'}
                  </button>
                </div>
              </div>
            )}

            {/* Shop Tab */}
            {activeTab === 'shop' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Shop Items</h2>
                <p className="text-gray-600 mb-6">Scrape all items from a specific shop</p>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Shop ID *
                    </label>
                    <input
                      type="text"
                      value={shopId}
                      onChange={(e) => setShopId(e.target.value)}
                      placeholder="e.g., 88069863"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">Find this in the shop URL</p>
                  </div>

                  <div className="space-y-3">
                    <label className="flex items-center gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={includeActive}
                        onChange={(e) => setIncludeActive(e.target.checked)}
                        className="w-5 h-5 text-orange-500 rounded focus:ring-orange-500"
                      />
                      <div>
                        <p className="font-medium text-gray-800">Include Active Items</p>
                        <p className="text-xs text-gray-500">Products currently available for purchase</p>
                      </div>
                    </label>

                    <label className="flex items-center gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={includeSoldOut}
                        onChange={(e) => setIncludeSoldOut(e.target.checked)}
                        className="w-5 h-5 text-orange-500 rounded focus:ring-orange-500"
                      />
                      <div>
                        <p className="font-medium text-gray-800">Include Sold-Out Items</p>
                        <p className="text-xs text-gray-500">Products no longer in stock</p>
                      </div>
                    </label>
                  </div>

                  <button
                    onClick={handleShopScrape}
                    disabled={isRunning || !shopId || (!includeActive && !includeSoldOut) || !driverInitialized}
                    className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-3 px-6 rounded-lg font-semibold hover:from-orange-600 hover:to-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isRunning ? <Loader2 className="animate-spin" size={20} /> : <Play size={20} />}
                    {isRunning ? 'Scraping...' : 'Start Scraping'}
                  </button>
                </div>
              </div>
            )}

            {/* Reviews Tab */}
            {activeTab === 'reviews' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Scrape Reviews</h2>
                <p className="text-gray-600 mb-6">Extract reviews from products in a CSV file</p>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Product List CSV *
                    </label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-orange-500 transition-colors">
                      <input
                        type="file"
                        accept=".csv"
                        onChange={(e) => setReviewsFile(e.target.files[0])}
                        className="hidden"
                        id="reviews-file"
                      />
                      <label htmlFor="reviews-file" className="cursor-pointer">
                        <Download className="mx-auto mb-2 text-gray-400" size={40} />
                        <p className="text-sm font-medium text-gray-700">
                          {reviewsFile ? reviewsFile.name : 'Click to upload CSV file'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Must contain: Shop ID, Item ID, Product Name
                        </p>
                      </label>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Reviews per Product
                    </label>
                    <input
                      type="number"
                      value={maxReviews}
                      onChange={(e) => setMaxReviews(Number(e.target.value))}
                      min="1"
                      max="10000"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    />
                  </div>

                  <button
                    onClick={handleReviewsScrape}
                    disabled={isRunning || !reviewsFile || !driverInitialized}
                    className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-3 px-6 rounded-lg font-semibold hover:from-orange-600 hover:to-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isRunning ? <Loader2 className="animate-spin" size={20} /> : <Play size={20} />}
                    {isRunning ? 'Scraping...' : 'Start Scraping'}
                  </button>
                </div>
              </div>
            )}

            {/* Analyze Tab */}
            {activeTab === 'analyze' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Analyze Reviews</h2>
                <p className="text-gray-600 mb-6">Perform sentiment analysis and generate insights</p>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Reviews CSV File *
                    </label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-orange-500 transition-colors">
                      <input
                        type="file"
                        accept=".csv"
                        onChange={(e) => setAnalyzeFile(e.target.files[0])}
                        className="hidden"
                        id="analyze-file"
                      />
                      <label htmlFor="analyze-file" className="cursor-pointer">
                        <Download className="mx-auto mb-2 text-gray-400" size={40} />
                        <p className="text-sm font-medium text-gray-700">
                          {analyzeFile ? analyzeFile.name : 'Click to upload CSV file'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Must contain: Product Name, Comment, Rating, Tags
                        </p>
                      </label>
                    </div>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-900 mb-2">Analysis Features:</h3>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>• Sentiment analysis (Positive/Neutral/Negative)</li>
                      <li>• Consensus scoring (0-100)</li>
                      <li>• Word cloud generation</li>
                      <li>• Top keywords extraction</li>
                      <li>• Rating distribution analysis</li>
                    </ul>
                  </div>

                  <button
                    onClick={handleAnalyze}
                    disabled={isRunning || !analyzeFile}
                    className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-3 px-6 rounded-lg font-semibold hover:from-orange-600 hover:to-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isRunning ? <Loader2 className="animate-spin" size={20} /> : <BarChart3 size={20} />}
                    {isRunning ? 'Analyzing...' : 'Start Analysis'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Activity Log */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
                Activity Log
              </h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {logs.length === 0 ? (
                  <p className="text-gray-400 text-sm text-center py-8">No activity yet</p>
                ) : (
                  logs.map((log, idx) => <LogEntry key={idx} {...log} />)
                )}
              </div>
            </div>

            {/* Results */}
            {results && (
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl shadow-lg p-6 border-2 border-green-200">
                <h3 className="text-lg font-bold text-green-900 mb-4">Results</h3>
                <div className="space-y-3">
                  {results.output_file && (
                    <>
                      <div className="pt-3 border-t border-green-200">
                        <p className="text-xs text-green-600 mb-2">Output File:</p>
                        <p className="text-xs font-mono bg-white px-3 py-2 rounded border border-green-200 break-all">
                          {results.output_file.split('/').pop()}
                        </p>
                      </div>
                      <button 
                        onClick={() => downloadFile(results.output_file.split('/').pop())}
                        className="w-full bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2 mt-4"
                      >
                        <Download size={16} />
                        Download CSV
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Info Card */}
            <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl shadow-lg p-6 border-2 border-orange-200">
              <h3 className="text-lg font-bold text-orange-900 mb-3">💡 Quick Tips</h3>
              <ul className="text-sm text-orange-800 space-y-2">
                <li>• Initialize driver & login first</li>
                <li>• Start with small datasets</li>
                <li>• Delays prevent bot detection</li>
                <li>• Download results as CSV</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShopeeScraperUI;