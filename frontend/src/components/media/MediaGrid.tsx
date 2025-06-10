import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { MediaItem } from '@/types/media'

interface MediaGridProps {
  mediaItems: MediaItem[]
  isLoading: boolean
  viewMode?: 'grid' | 'list'
}

const MediaGrid = ({ mediaItems, isLoading, viewMode = 'grid' }: MediaGridProps) => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({})
  
  // 处理媒体点击
  const handleMediaClick = (media: MediaItem) => {
    const currentPage = searchParams.get('page') || '1'
    const activeTab = searchParams.get('tab') || 'all'
    navigate(`/media/view/${media.id}?from=${currentPage}&tab=${activeTab}`)
  }
  
  // 图片加载失败处理
  const handleImageError = (media: MediaItem) => {
    setImageErrors(prev => ({...prev, [media.id]: true}))
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 格式化日期
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  // 加载中状态
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }
  
  // 无媒体项
  if (mediaItems.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">暂无媒体文件</div>
      </div>
    )
  }
  
  return (
    <div className="relative">
      {viewMode === 'grid' ? (
        /* 平铺模式 - 网格布局 */
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {mediaItems.map((media) => (
            <div 
              key={media.id} 
              className="aspect-square overflow-hidden rounded-lg shadow-sm hover:shadow-md cursor-pointer transition-shadow"
              onClick={() => handleMediaClick(media)}
            >
              {media.type === 'video' ? (
                <div className="relative h-full w-full bg-gray-100">
                  <img 
                    src={media.thumbnail_url} 
                    alt={media.name}
                    className="h-full w-full object-cover"
                    loading="lazy"
                    onError={() => handleImageError(media)}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg 
                      className="h-12 w-12 text-white opacity-80" 
                      fill="currentColor" 
                      viewBox="0 0 20 20"
                    >
                      <path d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                    </svg>
                  </div>
                </div>
              ) : (
                <img 
                  src={imageErrors[media.id] ? media.url : media.thumbnail_url} 
                  alt={media.name}
                  className="h-full w-full object-cover"
                  loading="lazy"
                  onError={() => handleImageError(media)}
                />
              )}
            </div>
          ))}
        </div>
      ) : (
        /* 列表模式 - 列表布局 */
        <div className="space-y-2">
          {mediaItems.map((media) => (
            <div 
              key={media.id}
              className="flex items-center p-3 bg-white rounded-lg shadow-sm hover:shadow-md cursor-pointer transition-shadow border"
              onClick={() => handleMediaClick(media)}
            >
              {/* 左侧缩略图 */}
              <div className="flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden bg-gray-100">
                {media.type === 'video' ? (
                  <div className="relative h-full w-full">
                    <img 
                      src={media.thumbnail_url} 
                      alt={media.name}
                      className="h-full w-full object-cover"
                      loading="lazy"
                      onError={() => handleImageError(media)}
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <svg 
                        className="h-6 w-6 text-white opacity-80" 
                        fill="currentColor" 
                        viewBox="0 0 20 20"
                      >
                        <path d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                      </svg>
                    </div>
                  </div>
                ) : (
                  <img 
                    src={imageErrors[media.id] ? media.url : media.thumbnail_url} 
                    alt={media.name}
                    className="h-full w-full object-cover"
                    loading="lazy"
                    onError={() => handleImageError(media)}
                  />
                )}
              </div>

              {/* 右侧详细信息 */}
              <div className="ml-4 flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    {/* 文件名 */}
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {media.name}
                    </h3>
                    
                    {/* 详细信息 */}
                    <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                      <span className="flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        {formatFileSize(media.size)}
                      </span>
                      
                      <span className="flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-9 3v10a2 2 0 002 2h6a2 2 0 002-2V7H7z" />
                        </svg>
                        {media.type === 'photo' ? '照片' : '视频'}
                      </span>
                      
                      {media.width && media.height && (
                        <span className="flex items-center">
                          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V6a2 2 0 012-2h2M4 16v2a2 2 0 002 2h2m8-16h2a2 2 0 012 2v2m-4 12h2a2 2 0 002-2v-2" />
                          </svg>
                          {media.width} × {media.height}
                        </span>
                      )}
                      
                      <span className="flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {formatDate(media.upload_date)}
                      </span>
                    </div>
                  </div>

                  {/* 类型图标 */}
                  <div className="ml-4 flex-shrink-0">
                    {media.type === 'video' ? (
                      <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M2 6a2 2 0 012-2h6l2 2h6a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM5 8a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H5z" />
                        </svg>
                      </div>
                    ) : (
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default MediaGrid 