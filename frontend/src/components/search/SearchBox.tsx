import { useState, useRef } from 'react'
import { SearchIcon, XIcon, CameraIcon } from '@heroicons/react/outline'

interface SearchBoxProps {
  onSearch: (query: string) => void;
  onImageSearch?: (file: File) => void;
  onClear: () => void;
  placeholder?: string;
  className?: string;
  isLoading?: boolean;
}

const SearchBox = ({ 
  onSearch, 
  onImageSearch,
  onClear, 
  placeholder = "搜索照片和视频...", 
  className = "",
  isLoading = false 
}: SearchBoxProps) => {
  const [query, setQuery] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query.trim())
    }
  }

  const handleClear = () => {
    setQuery('')
    onClear()
  }

  const handleCameraClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && onImageSearch) {
      // 验证文件类型
      if (file.type.startsWith('image/')) {
        onImageSearch(file)
      } else {
        alert('请选择图片文件')
      }
    }
    // 清空input值，允许重复选择同一文件
    e.target.value = ''
  }

  return (
    <form onSubmit={handleSubmit} className={`relative ${className}`}>
      <div className="relative rounded-md shadow-sm">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <SearchIcon 
            className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''} text-gray-400`} 
            aria-hidden="true" 
          />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 pr-20 sm:text-sm border-gray-300 rounded-md"
          placeholder={placeholder}
          disabled={isLoading}
        />
        <div className="absolute inset-y-0 right-0 flex items-center">
          {/* 以图搜图按钮 */}
          {onImageSearch && (
            <button
              type="button"
              onClick={handleCameraClick}
              disabled={isLoading}
              className="mr-2 p-1 text-gray-400 hover:text-primary-600 focus:outline-none focus:text-primary-600 transition-colors"
              title="以图搜图"
            >
              <CameraIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          )}
          
          {/* 清除按钮 */}
          {query && (
            <button
              type="button"
              onClick={handleClear}
              disabled={isLoading}
              className="mr-3 text-gray-400 hover:text-gray-600 focus:outline-none"
              title="清除搜索"
            >
              <XIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
      
      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />
    </form>
  )
}

export default SearchBox 