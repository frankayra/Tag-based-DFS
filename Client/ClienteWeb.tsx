'use client'

import { useState } from 'react'
import { Search, Send } from 'lucide-react'

export default function ClienteWeb() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<string[]>([])
  const [isSearching, setIsSearching] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSearching(true)
    // Aquí deberías hacer la llamada a tu endpoint Python
    // Por ahora, simularemos una respuesta después de un breve retraso
    setTimeout(() => {
      setResults([`Resultado para: ${query}`, 'Otro resultado', 'Un tercer resultado'])
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center transition-all duration-300 ease-in-out px-[50px]">
      <h1 
        className={`text-3xl font-bold mt-20 mb-8 transition-all duration-300 ease-in-out text-center ${
          isSearching ? 'opacity-0 h-0 mt-0 mb-0' : 'opacity-100'
        }`}
      >
        Haga sus consultas a nuestro sistema
      </h1>
      <div className={`w-full max-w-3xl transition-all duration-300 ease-in-out ${
        isSearching ? 'mt-4' : 'mt-20'
      }`}>
        <form onSubmit={handleSubmit} className="flex items-center bg-white rounded-full shadow-lg overflow-hidden relative">
          <div className="p-3 pl-4">
            <Search className="h-6 w-6 text-gray-500" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-grow px-2 py-3 bg-transparent focus:outline-none pr-16"
            placeholder="Escriba su consulta aquí..."
          />
          <button 
            type="submit" 
            className="absolute right-0 top-0 bottom-0 bg-gray-800 text-white px-4 focus:outline-none hover:bg-gray-700 transition-colors duration-200"
            aria-label="Enviar consulta"
          >
            <Send className="h-6 w-6" />
          </button>
        </form>
      </div>
      <div className={`w-full max-w-3xl mt-8 transition-all duration-300 ease-in-out ${
        isSearching ? 'opacity-100' : 'opacity-0'
      }`}>
        {results.map((result, index) => (
          <div key={index} className="bg-white p-4 rounded-lg shadow-md mb-4">
            {result}
          </div>
        ))}
      </div>
    </div>
  )
}