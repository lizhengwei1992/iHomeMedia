import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../services/api'
import axios from 'axios'

// 认证上下文类型
interface AuthContextType {
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  login: async () => false,
  logout: () => {},
})

// 认证提供者属性类型
interface AuthProviderProps {
  children: ReactNode
}

// 认证提供者组件
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)

  // 检查是否已认证
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      setIsAuthenticated(true)
      // 设置axios默认请求头
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }, [])

  // 登录方法
  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      // 使用authApi服务进行认证
      const response = await authApi.login(username, password)
      const { access_token } = response.data
      
      if (access_token) {
        localStorage.setItem('token', access_token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        setIsAuthenticated(true)
        return true
      }
      return false
    } catch (error) {
      console.error('登录失败:', error)
      return false
    }
  }

  // 登出方法
  const logout = () => {
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// 使用认证钩子
export const useAuth = () => useContext(AuthContext) 