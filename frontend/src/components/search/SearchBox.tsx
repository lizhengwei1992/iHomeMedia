import { useState } from 'react'
import { SearchIcon, XIcon } from '@heroicons/react/outline'

interface SearchBoxProps {
  onSearch: (query: string) => void;
  onClear: () => void;
  placeholder?: string;
  className?: string;
  isLoading?: boolean;
}

const SearchBox = ({ 
  onSearch, 
  onClear, 
  placeholder = "搜索照片和视频...", 
  className = "",
  isLoading = false 
}: SearchBoxProps) => {
  const [query, setQuery] = useState('')

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
          className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 pr-12 sm:text-sm border-gray-300 rounded-md"
          placeholder={placeholder}
          disabled={isLoading}
        />
        {query && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <button
              type="button"
              onClick={handleClear}
              disabled={isLoading}
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <XIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </form>
  )
}

export default SearchBox 