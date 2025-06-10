import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { MediaItem } from '@/types/media'
import MediaGrid from '@/components/media/MediaGrid'
import Pagination from '@/components/common/Pagination'
import { InformationCircleIcon } from '@heroicons/react/outline'

interface SearchResult {
  media_id: string;
  score: number;
  metadata: {
    global_media_id: string;
    file_path: string;
    file_name: string;
    file_type: string;
    file_size: number;
    upload_time: string;
    description?: string;
    original_url?: string;
    thumbnail_url?: string;
    relative_path?: string;
    file_id?: string;
    original_name?: string;
    width?: number;
    height?: number;
  };
}

const SearchResultsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  
  // 从URL参数获取搜索结果
  const query = searchParams.get('query') || ''
  const resultsJson = searchParams.get('results')
  const totalResults = parseInt(searchParams.get('total_results') || '0')
  const searchTime = parseFloat(searchParams.get('search_time') || '0')
  
  // 页面状态
  const [allResults, setAllResults] = useState<SearchResult[]>([])
  const [displayedResults, setDisplayedResults] = useState<SearchResult[]>([])
  const [currentPage, setCurrentPage] = useState(
    parseInt(searchParams.get('page') || '1')
  )
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const pageSize = 10 // 每页10个结果
  const [totalPages, setTotalPages] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  // 初始化搜索结果
  useEffect(() => {
    if (resultsJson) {
      try {
        const results: SearchResult[] = JSON.parse(resultsJson)
        // 按score从高到低排序
        const sortedResults = results.sort((a, b) => b.score - a.score)
        setAllResults(sortedResults)
        setTotalPages(Math.ceil(sortedResults.length / pageSize))
        console.log('🔍 搜索结果页面初始化:', {
          query,
          totalResults: sortedResults.length,
          searchTime
        })
      } catch (err) {
        console.error('解析搜索结果失败:', err)
        setAllResults([])
      }
    }
    setIsLoading(false)
  }, [resultsJson])

  // 更新当前页显示的结果
  useEffect(() => {
    const startIndex = (currentPage - 1) * pageSize
    const endIndex = startIndex + pageSize
    setDisplayedResults(allResults.slice(startIndex, endIndex))
  }, [allResults, currentPage, pageSize])

  // 转换搜索结果为MediaItem格式
  const convertToMediaItems = (searchResults: SearchResult[]): MediaItem[] => {
    return searchResults.map(result => {
      const metadata = result.metadata;
      
      const fileName = metadata.file_name || '未知文件';
      const fileType = metadata.file_type || 'photo';
      const filePath = metadata.relative_path || metadata.file_path || '';
      const fileSize = metadata.file_size || 0;
      const uploadTime = metadata.upload_time || '';
      const description = metadata.description || '';
      
      const originalUrl = metadata.original_url || `/media/${filePath}`;
      const thumbnailUrl = metadata.thumbnail_url || `/media/${filePath}`;
      
      const mediaId = metadata.file_id || fileName;
      
      return {
        id: mediaId,
        name: fileName,
        type: fileType.toLowerCase() as 'photo' | 'video',
        path: filePath,
        size: fileSize,
        url: originalUrl,
        thumbnail_url: thumbnailUrl,
        upload_date: uploadTime,
        description: description,
        score: result.score || 0,
        width: metadata.width,
        height: metadata.height,
        global_media_id: metadata.global_media_id || result.media_id,
      }
    })
  }

  // 处理页码变化
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    setSearchParams({
      query,
      results: resultsJson || '',
      total_results: totalResults.toString(),
      search_time: searchTime.toString(),
      page: page.toString()
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // 处理返回
  const handleBack = () => {
    navigate('/')
  }

  // 处理媒体项点击
  const handleMediaClick = (mediaItem: MediaItem) => {
    // 构建搜索结果的媒体列表，传递给媒体查看页面
    const searchResultItems = convertToMediaItems(allResults)
    const currentIndex = searchResultItems.findIndex(item => item.id === mediaItem.id)
    
    // 将搜索结果信息通过URL参数传递
    const params = new URLSearchParams({
      from_search: 'true',
      search_query: query,
      search_results: JSON.stringify(allResults),
      search_index: currentIndex.toString(),
      page: currentPage.toString()
    })
    
    navigate(`/media/view/${mediaItem.id}?${params.toString()}`)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-3 text-gray-600">加载中...</span>
      </div>
    )
  }

  if (allResults.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <button
                  onClick={handleBack}
                  className="mr-4 p-2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <h1 className="text-xl font-bold text-primary-700">搜索结果</h1>
              </div>
            </div>
          </div>
        </header>
        
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center py-12">
            <InformationCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">没有找到相关内容</h3>
            <p className="mt-1 text-sm text-gray-500">
              尝试使用不同的关键词，或检查拼写是否正确
            </p>
          </div>
        </main>
      </div>
    )
  }

  const mediaItems = convertToMediaItems(displayedResults)

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 顶部导航栏 */}
      <header className="bg-white shadow-sm flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={handleBack}
                className="mr-4 p-2 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-xl font-bold text-primary-700">搜索结果</h1>
            </div>
            
            {/* 显示模式选择器 */}
            <div className="flex items-center">
              <div className="relative">
                <select
                  value={viewMode}
                  onChange={(e) => setViewMode(e.target.value as 'grid' | 'list')}
                  className="appearance-none bg-white border border-gray-300 rounded-md pl-8 pr-8 py-1 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 cursor-pointer"
                >
                  <option value="grid">平铺</option>
                  <option value="list">列表</option>
                </select>
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
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-gray-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 主内容区域 */}
      <div className="flex-1">
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* 搜索结果统计 */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
            <div className="flex items-center">
              <InformationCircleIcon className="h-5 w-5 text-blue-400" />
              <div className="ml-3">
                <p className="text-sm text-blue-800">
                  搜索 "<span className="font-medium">{query}</span>" 找到 <span className="font-medium">{totalResults}</span> 个结果
                  {searchTime > 0 && (
                    <span className="text-blue-600">
                      ，用时 {searchTime.toFixed(2)}s
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* 媒体网格 */}
          <div className="mb-6">
            <MediaGrid 
              mediaItems={mediaItems} 
              isLoading={false}
              viewMode={viewMode}
              onItemClick={handleMediaClick}
            />
          </div>
          
          {/* 分页组件 */}
          {totalPages > 1 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={allResults.length}
              pageSize={pageSize}
              onPageChange={handlePageChange}
              isLoading={false}
            />
          )}
        </main>
      </div>
    </div>
  )
}

export default SearchResultsPage
