import React, { useRef, useState, useEffect, ReactNode } from 'react'

interface PullToRefreshProps {
  onRefresh: () => Promise<void>
  children: ReactNode
  disabled?: boolean
}

const PullToRefresh: React.FC<PullToRefreshProps> = ({ 
  onRefresh, 
  children, 
  disabled = false 
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [pulling, setPulling] = useState(false)
  const [pullDistance, setPullDistance] = useState(0)
  const [refreshing, setRefreshing] = useState(false)
  const [startY, setStartY] = useState(0)
  const [canPull, setCanPull] = useState(false)

  const PULL_THRESHOLD = 60 // 触发刷新的距离
  const MAX_PULL_DISTANCE = 100 // 最大下拉距离

  // 检查是否可以下拉（页面在顶部）
  const checkCanPull = () => {
    if (!containerRef.current) return false
    const scrollTop = containerRef.current.scrollTop
    // 更严格的判断：必须完全在顶部，并且没有正在滚动
    return scrollTop === 0 && !pulling
  }

  // 处理触摸开始
  const handleTouchStart = (e: TouchEvent) => {
    if (disabled || refreshing) return
    
    // 只有在页面完全在顶部且没有正在下拉时才记录起始位置
    if (checkCanPull() && containerRef.current?.scrollTop === 0) {
      setStartY(e.touches[0].clientY)
      setPulling(false)
      setPullDistance(0)
      setCanPull(false) // 先设置为false，在move中再判断
    } else {
      setCanPull(false)
      setStartY(0)
    }
  }

  // 处理触摸移动
  const handleTouchMove = (e: TouchEvent) => {
    if (disabled || refreshing || startY === 0) return

    const currentY = e.touches[0].clientY
    const deltaY = currentY - startY

    // 必须满足更严格的条件：1.有起始位置 2.明显向下拖拽(>15px) 3.页面在顶部 4.没有正在下拉
    if (startY > 0 && deltaY > 15 && containerRef.current?.scrollTop === 0 && !pulling) {
      // 阻止默认的页面滚动和下拉刷新
      e.preventDefault()
      
      if (!canPull) {
        setCanPull(true)
      }
      
      setPulling(true)
      const distance = Math.min(deltaY * 0.5, MAX_PULL_DISTANCE)
      setPullDistance(distance)
    } else if (deltaY <= 10 || containerRef.current?.scrollTop !== 0) {
      // 如果向上拖拽、小幅度移动或者页面不在顶部，重置状态
      if (canPull || pulling) {
        setCanPull(false)
        setPulling(false)
        setPullDistance(0)
      }
    }
  }

  // 处理触摸结束
  const handleTouchEnd = () => {
    if (disabled || refreshing) return

    if (canPull && pullDistance >= PULL_THRESHOLD) {
      handleRefresh()
    } else {
      // 重置状态
      setPulling(false)
      setPullDistance(0)
    }
    setCanPull(false)
    setStartY(0)
  }

  // 执行刷新
  const handleRefresh = async () => {
    setRefreshing(true)
    setPulling(false)
    
    try {
      await onRefresh()
    } catch (error) {
      console.error('刷新失败:', error)
    } finally {
      // 延迟重置状态，提供视觉反馈
      setTimeout(() => {
        setRefreshing(false)
        setPullDistance(0)
      }, 500)
    }
  }

  // 处理鼠标开始
  const handleMouseStart = (e: MouseEvent) => {
    if (disabled || refreshing) return
    
    // 只有在页面完全在顶部且没有正在下拉时才记录起始位置
    if (checkCanPull() && containerRef.current?.scrollTop === 0) {
      setStartY(e.clientY)
      setPulling(false)
      setPullDistance(0)
      setCanPull(false) // 先设置为false，在move中再判断
    } else {
      setCanPull(false)
      setStartY(0)
    }
  }

  // 处理鼠标移动
  const handleMouseMove = (e: MouseEvent) => {
    if (disabled || refreshing || startY === 0) return

    const currentY = e.clientY
    const deltaY = currentY - startY

    // 必须满足更严格的条件：1.有起始位置 2.明显向下拖拽(>15px) 3.页面在顶部 4.没有正在下拉
    if (startY > 0 && deltaY > 15 && containerRef.current?.scrollTop === 0 && !pulling) {
      e.preventDefault()
      
      if (!canPull) {
        setCanPull(true)
      }
      
      setPulling(true)
      const distance = Math.min(deltaY * 0.5, MAX_PULL_DISTANCE)
      setPullDistance(distance)
    } else if (deltaY <= 10 || containerRef.current?.scrollTop !== 0) {
      // 如果向上拖拽、小幅度移动或者页面不在顶部，重置状态
      if (canPull || pulling) {
        setCanPull(false)
        setPulling(false)
        setPullDistance(0)
      }
    }
  }

  // 处理鼠标结束
  const handleMouseEnd = () => {
    if (disabled || refreshing) return

    if (canPull && pullDistance >= PULL_THRESHOLD) {
      handleRefresh()
    } else {
      setPulling(false)
      setPullDistance(0)
    }
    setCanPull(false)
    setStartY(0)
  }

  // 添加触摸和鼠标事件监听器
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // 触摸事件
    container.addEventListener('touchstart', handleTouchStart, { passive: false })
    container.addEventListener('touchmove', handleTouchMove, { passive: false })
    container.addEventListener('touchend', handleTouchEnd, { passive: true })

    // 鼠标事件（用于桌面端测试）
    container.addEventListener('mousedown', handleMouseStart, { passive: false })
    document.addEventListener('mousemove', handleMouseMove, { passive: false })
    document.addEventListener('mouseup', handleMouseEnd, { passive: true })

    return () => {
      // 清理触摸事件
      container.removeEventListener('touchstart', handleTouchStart)
      container.removeEventListener('touchmove', handleTouchMove)
      container.removeEventListener('touchend', handleTouchEnd)
      
      // 清理鼠标事件
      container.removeEventListener('mousedown', handleMouseStart)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseEnd)
    }
  }, [disabled, refreshing, canPull, startY, pullDistance])

  // 计算刷新指示器的样式
  const indicatorStyle = {
    transform: `translateY(${Math.max(0, pullDistance - 40)}px)`,
    opacity: pullDistance > 10 ? Math.min(pullDistance / PULL_THRESHOLD, 1) : 0,
  }

  return (
    <div 
      ref={containerRef}
      className="relative h-full overflow-auto"
      style={{ 
        overscrollBehavior: 'none', // 阻止默认的过度滚动行为
        WebkitOverflowScrolling: 'touch'
      }}
    >
      {/* 下拉刷新指示器 */}
      <div 
        className="absolute top-0 left-0 right-0 flex justify-center items-center z-10 pointer-events-none"
        style={{
          height: '40px',
          marginTop: '-40px',
          ...indicatorStyle
        }}
      >
        <div className="flex items-center space-x-2 text-primary-600">
          {refreshing ? (
            <>
              <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span className="text-sm">刷新中...</span>
            </>
          ) : pullDistance >= PULL_THRESHOLD ? (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              <span className="text-sm">松开刷新</span>
            </>
          ) : pulling ? (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
              <span className="text-sm">下拉刷新</span>
            </>
          ) : null}
        </div>
      </div>

      {/* 内容区域 */}
      <div style={{ transform: `translateY(${refreshing ? 40 : 0}px)` }}>
        {children}
      </div>
    </div>
  )
}

export default PullToRefresh 