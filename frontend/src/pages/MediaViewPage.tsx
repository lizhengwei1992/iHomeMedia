import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { MediaItem } from '@/types/media'
import { mediaApi } from '@/services/api'

const MediaViewPage = () => {
  const { mediaId } = useParams<{ mediaId: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [media, setMedia] = useState<MediaItem | null>(null)
  const [allMedia, setAllMedia] = useState<MediaItem[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)
  const [renderKey, setRenderKey] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [description, setDescription] = useState('')
  const [isEditingDescription, setIsEditingDescription] = useState(false)
  const [tempDescription, setTempDescription] = useState('')
  
  const containerRef = useRef<HTMLDivElement>(null)
  const touchStartRef = useRef<{ x: number; y: number } | null>(null)

  // 获取URL参数
  const fromPage = searchParams.get('from') || '1'
  const mediaType = searchParams.get('type') || 'all'
  const activeTab = searchParams.get('tab') || 'all'

  // 获取媒体数据
  useEffect(() => {
    const loadMediaData = async () => {
      try {
        setIsLoading(true)
        setError('')
        setMedia(null) // 清空当前媒体状态
        setRenderKey(prev => prev + 1)

        // 获取媒体列表
        const response = await mediaApi.getList({
          page: 1,
          page_size: 100, // 获取更多数据以支持切换（后端限制最大100）
          ...(activeTab !== 'all' && { 
            media_type: activeTab === 'photos' ? 'photo' : 'video' 
          }),
        })

        const mediaList = response.data.items || []
        setAllMedia(mediaList)

        // 查找当前媒体项
        const currentMediaIndex = mediaList.findIndex((item: MediaItem) => item.id === mediaId)
        
        if (currentMediaIndex >= 0) {
          setMedia(mediaList[currentMediaIndex])
          setCurrentIndex(currentMediaIndex)
          // 初始化描述（从服务器获取）
          setDescription(mediaList[currentMediaIndex].description || '')
          setTimeout(() => {
            setIsLoading(false)
          }, 10)
        } else {
          setError('媒体文件未找到')
          setIsLoading(false)
        }
      } catch (err) {
        console.error('加载媒体失败:', err)
        setError('加载媒体失败')
        setIsLoading(false)
      }
    }

    if (mediaId) {
      loadMediaData()
    }
  }, [mediaId, activeTab])

  // 处理返回
  const handleBack = () => {
    navigate(`/?page=${fromPage}&tab=${activeTab}`)
  }

  // 处理下载
  const handleDownload = () => {
    if (!media) return
    
    const link = document.createElement('a')
    link.href = media.url
    link.download = media.name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 处理删除
  const handleDelete = async () => {
    if (!media) return
    
    const confirmed = window.confirm(`确定要删除这个媒体文件吗？此操作无法撤销。`)
    if (!confirmed) return

    setIsDeleting(true)
    try {
      await mediaApi.delete(media.id)
      
      // 删除成功后，如果还有其他媒体，切换到下一个，否则返回列表
      const newMediaList = allMedia.filter((item: MediaItem) => item.id !== media.id)
      
      if (newMediaList.length > 0) {
        // 优先显示下一个，如果是最后一个则显示上一个
        const nextIndex = currentIndex < newMediaList.length ? currentIndex : currentIndex - 1
        const nextMedia = newMediaList[nextIndex]
        
        // 更新URL
        navigate(`/media/view/${nextMedia.id}?from=${fromPage}&tab=${activeTab}&type=${mediaType}`, { replace: true })
      } else {
        // 没有更多媒体，返回列表
        handleBack()
      }
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败，请重试')
    } finally {
      setIsDeleting(false)
    }
  }

  // 切换到上一个媒体
  const handlePrevious = () => {
    if (currentIndex > 0) {
      const prevMedia = allMedia[currentIndex - 1]
      navigate(`/media/view/${prevMedia.id}?from=${fromPage}&tab=${activeTab}&type=${mediaType}`, { replace: true })
    }
  }

  // 切换到下一个媒体
  const handleNext = () => {
    if (currentIndex < allMedia.length - 1) {
      const nextMedia = allMedia[currentIndex + 1]
      navigate(`/media/view/${nextMedia.id}?from=${fromPage}&tab=${activeTab}&type=${mediaType}`, { replace: true })
    }
  }

  // 全屏相关功能
  const handleImageClick = () => {
    if (media?.type === 'photo') {
      setIsFullscreen(true)
    }
  }

  const handleFullscreenClose = () => {
    setIsFullscreen(false)
  }

  // 描述编辑相关功能
  const handleDescriptionClick = () => {
    setTempDescription(description)
    setIsEditingDescription(true)
  }

  const handleDescriptionSave = async () => {
    if (!media) return
    
    try {
      await mediaApi.updateDescription(media.id, tempDescription)
      setDescription(tempDescription)
      setIsEditingDescription(false)
    } catch (error) {
      console.error('保存描述失败:', error)
      alert('保存描述失败，请重试')
    }
  }

  const handleDescriptionCancel = () => {
    setTempDescription('')
    setIsEditingDescription(false)
  }

  // 触摸事件处理
  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0]
    touchStartRef.current = { x: touch.clientX, y: touch.clientY }
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!touchStartRef.current) return

    const touch = e.changedTouches[0]
    const deltaX = touch.clientX - touchStartRef.current.x
    const deltaY = touch.clientY - touchStartRef.current.y

    // 水平滑动距离大于垂直滑动距离，且滑动距离超过50px
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
      if (deltaX > 0) {
        // 向右滑动 - 上一张
        handlePrevious()
      } else {
        // 向左滑动 - 下一张
        handleNext()
      }
    }

    touchStartRef.current = null
  }

  // 键盘事件处理
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isEditingDescription) return
      
      switch (e.key) {
        case 'Escape':
          if (isFullscreen) {
            handleFullscreenClose()
          } else {
            handleBack()
          }
          break
        case 'ArrowLeft':
          if (!isFullscreen) handlePrevious()
          break
        case 'ArrowRight':
          if (!isFullscreen) handleNext()
          break
        case 'Delete':
          if (!isFullscreen) handleDelete()
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentIndex, allMedia, isFullscreen, isEditingDescription])

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

  if (isLoading) {
    return (
      <div key={`loading-${renderKey}`} className="fixed inset-0 bg-black flex items-center justify-center">
        <div className="text-white text-lg">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div key={`error-${renderKey}`} className="fixed inset-0 bg-black flex flex-col items-center justify-center">
        <div className="text-white text-lg mb-4">{error}</div>
        <button
          onClick={handleBack}
          className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          返回列表
        </button>
      </div>
    )
  }

  if (!media) {
    return (
      <div key={`no-media-${renderKey}`} className="fixed inset-0 bg-black flex items-center justify-center">
        <div className="text-white text-lg">媒体文件未找到</div>
      </div>
    )
  }

  return (
    <>
      <div key={`media-view-${renderKey}`} className="fixed inset-0 bg-black overflow-hidden">
        {/* 顶部导航栏 */}
        <div className="absolute top-0 left-0 right-0 z-20 bg-gradient-to-b from-black/70 to-transparent">
          <div className="flex items-center justify-between p-4">
            <button
              onClick={handleBack}
              className="flex items-center text-white hover:text-gray-300 transition-colors"
            >
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              返回
            </button>

            <div className="text-white text-sm">
              {currentIndex + 1} / {allMedia.length}
            </div>

            <div className="flex items-center space-x-3">
              {/* 下载按钮 */}
              <button
                onClick={handleDownload}
                className="text-white hover:text-gray-300 transition-colors"
                title="下载"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </button>

              {/* 删除按钮 */}
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="text-white hover:text-red-400 transition-colors disabled:opacity-50"
                title="删除"
              >
                {isDeleting ? (
                  <svg className="w-6 h-6 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 主要内容区域 */}
        <div 
          ref={containerRef}
          className="flex items-center justify-center h-full relative"
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          {/* 左右切换按钮 (桌面端) */}
          {currentIndex > 0 && (
            <button
              onClick={handlePrevious}
              className="absolute left-4 top-1/2 transform -translate-y-1/2 z-10 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-colors hidden md:block"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}

          {currentIndex < allMedia.length - 1 && (
            <button
              onClick={handleNext}
              className="absolute right-4 top-1/2 transform -translate-y-1/2 z-10 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-colors hidden md:block"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}

          {/* 媒体内容 */}
          <div className="max-w-full max-h-full p-4 pt-20 pb-32">
            {media.type === 'video' ? (
              <video
                key={`video-${media.id}-${renderKey}`}
                src={media.url}
                controls
                autoPlay
                className="max-h-full max-w-full object-contain"
                controlsList="nodownload"
                playsInline
              />
            ) : (
              <img
                key={`image-${media.id}-${renderKey}`}
                src={media.url}
                alt={media.name}
                className="max-h-full max-w-full object-contain cursor-pointer"
                onClick={handleImageClick}
                onLoad={() => {
                  if (containerRef.current) {
                    containerRef.current.style.display = 'none'
                    containerRef.current.offsetHeight
                    containerRef.current.style.display = 'flex'
                  }
                }}
              />
            )}
          </div>
        </div>

        {/* 底部信息栏 */}
        <div className="absolute bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-black/70 to-transparent">
          <div className="p-4 text-white">
            {/* 媒体描述区域 */}
            <div className="mb-4">
              {isEditingDescription ? (
                <div className="space-y-2">
                  <textarea
                    value={tempDescription}
                    onChange={(e) => setTempDescription(e.target.value)}
                    placeholder="添加媒体内容说明..."
                    className="w-full bg-black/50 text-white border border-gray-600 rounded px-3 py-2 resize-none focus:outline-none focus:border-blue-500"
                    rows={3}
                    autoFocus
                  />
                  <div className="flex space-x-2">
                    <button
                      onClick={handleDescriptionSave}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                    >
                      保存
                    </button>
                    <button
                      onClick={handleDescriptionCancel}
                      className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
                    >
                      取消
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  onClick={handleDescriptionClick}
                  className="cursor-pointer hover:bg-black/30 rounded p-2 transition-colors min-h-[40px] flex items-center"
                >
                  {description ? (
                    <p className="text-gray-200">{description}</p>
                  ) : (
                    <p className="text-gray-400 italic">点击添加媒体内容说明...</p>
                  )}
                </div>
              )}
            </div>

            {/* 文件信息 */}
            <div className="flex flex-wrap gap-4 text-sm text-gray-300">
              <span>{formatFileSize(media.size)}</span>
              <span>{media.type === 'photo' ? '照片' : '视频'}</span>
              {media.width && media.height && (
                <span>{media.width} × {media.height}</span>
              )}
              <span>{formatDate(media.upload_date)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 全屏图片查看器 */}
      {isFullscreen && media?.type === 'photo' && (
        <div className="fixed inset-0 bg-black z-50 flex items-center justify-center">
          <button
            onClick={handleFullscreenClose}
            className="absolute top-4 right-4 z-60 text-white hover:text-gray-300 transition-colors"
          >
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <img
            src={media.url}
            alt={media.name}
            className="max-w-full max-h-full object-contain"
            onClick={handleFullscreenClose}
          />
        </div>
      )}
    </>
  )
}

export default MediaViewPage 