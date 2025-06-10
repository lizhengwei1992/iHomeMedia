import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { mediaApi, searchApi } from '@/services/api'
import { MediaItem } from '@/types/media'
import MediaGrid from '@/components/media/MediaGrid'
import UploadForm from '@/components/media/UploadForm'
import PullToRefresh from '@/components/common/PullToRefresh'
import Pagination from '@/components/common/Pagination'
import SearchBox from '@/components/search/SearchBox'
import SearchResults from '@/components/search/SearchResults'

const HomePage = () => {
  const { logout } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [mediaItems, setMediaItems] = useState<MediaItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [currentPage, setCurrentPage] = useState(
    parseInt(searchParams.get('page') || '1')
  )
  const [totalPages, setTotalPages] = useState(0)
  const [totalItems, setTotalItems] = useState(0)
  const pageSize = 20 // 每页显示20个文件
  const [activeTab, setActiveTab] = useState<'all' | 'photos' | 'videos'>(
    (searchParams.get('tab') as 'all' | 'photos' | 'videos') || 'all'
  )
  const [showUpload, setShowUpload] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [isPageChanging, setIsPageChanging] = useState(false) // 添加页面切换状态
  
  // 搜索相关状态
  const [isSearchMode, setIsSearchMode] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchStats, setSearchStats] = useState({
    totalResults: 0,
    searchTime: 0
  })
  
  // 加载媒体数据
  const loadMedia = async (page = currentPage) => {
    try {
      setIsLoading(true)
      setError('')
      
      const mediaType = activeTab === 'all' ? undefined : activeTab === 'photos' ? 'photo' : 'video'
      
      const response = await mediaApi.getList({
        page: page,
        page_size: pageSize,
        ...(mediaType && { media_type: mediaType }),
      })
      
      const data = response.data
      
      setMediaItems(data.items || [])
      setTotalItems(data.total || 0)
      setTotalPages(Math.ceil((data.total || 0) / pageSize))
      
    } catch (err) {
      console.error('加载媒体失败:', err)
      setError('加载媒体失败，请刷新重试')
    } finally {
      setIsLoading(false)
    }
  }
  
  // 首次加载
  useEffect(() => {
    loadMedia()
  }, [])
  
  // 监听页码变化
  useEffect(() => {
    loadMedia(currentPage)
  }, [currentPage, activeTab])

  // 处理标签切换
  const handleTabChange = (tab: 'all' | 'photos' | 'videos') => {
    setIsPageChanging(true)
    setActiveTab(tab)
    setCurrentPage(1)
    setSearchParams({ tab, page: '1' })
    // 切换标签后重置状态
    setTimeout(() => {
      setIsPageChanging(false)
    }, 500)
  }
  
  // 处理页码变化
  const handlePageChange = (page: number) => {
    setIsPageChanging(true)
    setCurrentPage(page)
    setSearchParams({ 
      tab: activeTab, 
      page: page.toString() 
    })
    // 延迟滚动到顶部，避免与用户滚动冲突
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' })
      // 重置页面切换状态
      setTimeout(() => {
        setIsPageChanging(false)
      }, 300)
    }, 100)
  }
  
  // 处理上传完成
  const handleUploadComplete = () => {
    // 上传完成后回到第一页
    setCurrentPage(1)
    setSearchParams({ tab: activeTab, page: '1' })
    loadMedia(1)
  }

  // 处理搜索
  const handleSearch = async (query: string) => {
    if (!query.trim()) return
    
    setIsSearching(true)
    setIsSearchMode(true)
    setSearchQuery(query)
    
    try {
      const response = await searchApi.searchByText({
        query: query,
        limit: 20
        // threshold参数已移除，后端使用配置的固定阈值(0.15)
      })
      
      const data = response.data
      
      // 添加调试日志
      console.log('🔍 搜索API响应:', {
        success: data.success,
        query: data.query,
        resultsCount: data.results?.length || 0,
        results: data.results?.slice(0, 2), // 仅显示前2个结果
        totalResults: data.total_results,
        searchTime: data.search_time
      });
      
      setSearchResults(data.results || [])
      setSearchStats({
        totalResults: data.total_results || 0,
        searchTime: data.search_time || 0
      })
    } catch (err) {
      console.error('搜索失败:', err)
      setSearchResults([])
      setSearchStats({ totalResults: 0, searchTime: 0 })
      setError('搜索失败，请稍后重试')
    } finally {
      setIsSearching(false)
    }
  }
  
  // 清空搜索
  const handleClearSearch = () => {
    setIsSearchMode(false)
    setSearchQuery('')
    setSearchResults([])
    setSearchStats({ totalResults: 0, searchTime: 0 })
    setError('')
  }


  
  // 处理下拉刷新
  const handleRefresh = async () => {
    await loadMedia(currentPage)
  }
  
  // 处理退出登录
  const handleLogout = () => {
    logout()
  }
  
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 顶部导航栏 */}
      <header className="bg-white shadow-sm flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-primary-700">家庭媒体库</h1>
              </div>
            </div>
            <div className="flex items-center">
              <button
                onClick={() => setShowUpload(!showUpload)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                {showUpload ? '隐藏上传' : '上传文件'}
              </button>
              <button
                onClick={handleLogout}
                className="ml-4 inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                退出登录
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* 主内容区域包装在下拉刷新组件中 */}
      <div className="flex-1 overflow-hidden">
        <PullToRefresh onRefresh={handleRefresh} disabled={isLoading || isPageChanging}>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 上传表单 */}
        {showUpload && (
          <div className="mb-6">
            <UploadForm onUploadComplete={handleUploadComplete} />
          </div>
        )}

        {/* 搜索框 */}
        <div className="mb-6">
          <SearchBox
            onSearch={handleSearch}
            onClear={handleClearSearch}
            isLoading={isSearching}
            placeholder="搜索照片和视频内容..."
          />
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* 搜索结果或正常列表 */}
        {isSearchMode ? (
          <SearchResults
            results={searchResults}
            isLoading={isSearching}
            query={searchQuery}
            searchTime={searchStats.searchTime}
            totalResults={searchStats.totalResults}
          />
        ) : (
          <>
        {/* 类型标签和刷新按钮 */}
        <div className="flex justify-between items-center border-b border-gray-200 mb-6">
          <div className="flex">
            <button
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'all'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => handleTabChange('all')}
            >
              全部
            </button>
            <button
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'photos'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => handleTabChange('photos')}
            >
              照片
            </button>
            <button
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'videos'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => handleTabChange('videos')}
            >
              视频
            </button>
          </div>
          
          <div className="flex items-center space-x-3">
            {/* 显示模式选择器 */}
            <div className="relative">
              <select
                value={viewMode}
                onChange={(e) => setViewMode(e.target.value as 'grid' | 'list')}
                className="appearance-none bg-white border border-gray-300 rounded-md pl-8 pr-8 py-1 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 cursor-pointer"
              >
                <option value="grid">平铺</option>
                <option value="list">列表</option>
              </select>
              {/* 左侧图标 */}
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-2 text-gray-500">
                {viewMode === 'grid' ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                )}
              </div>
              {/* 右侧下拉箭头 */}
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-gray-500">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            {/* 手动刷新按钮 */}
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-primary-600 disabled:opacity-50"
              title="刷新列表"
            >
              <svg 
                className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              刷新
            </button>
          </div>
        </div>
        
        {/* 错误信息 */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}
        
        {/* 媒体网格 */}
        <div className="mb-6">
          <MediaGrid 
            mediaItems={mediaItems} 
            isLoading={isLoading}
            viewMode={viewMode}
          />
        </div>
        
        {/* 分页组件 */}
        {totalPages > 1 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalItems}
            pageSize={pageSize}
            onPageChange={handlePageChange}
            isLoading={isLoading}
          />
        )}
        
        {/* 加载中指示器 - 仅在第一次加载时显示 */}
        {isLoading && mediaItems.length === 0 && (
          <div className="mt-6 flex justify-center">
            <div className="text-gray-500">加载中...</div>
          </div>
        )}

        {/* 无数据提示 */}
        {!isLoading && mediaItems.length === 0 && !error && (
          <div className="mt-12 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">暂无媒体文件</h3>
            <p className="mt-1 text-sm text-gray-500">
              {activeTab === 'all' ? '还没有上传任何文件' : 
               activeTab === 'photos' ? '还没有上传任何照片' : '还没有上传任何视频'}
            </p>
          </div>
        )}
        </>
        )}
          </main>
        </PullToRefresh>
      </div>
    </div>
  )
}

export default HomePage 