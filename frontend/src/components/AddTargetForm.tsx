import { useState } from 'react'

interface AddTargetFormProps {
  onSubmit: (data: {
    name: string
    url: string
    check_interval_seconds: number
  }) => void
  onCancel: () => void
  isLoading: boolean
}

export default function AddTargetForm({
  onSubmit,
  onCancel,
  isLoading,
}: AddTargetFormProps) {
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [interval, setInterval] = useState('300')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      name,
      url,
      check_interval_seconds: parseInt(interval, 10),
    })
    setName('')
    setUrl('')
    setInterval('300')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 mb-6 p-4 bg-blue-50 rounded-lg">
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          Target Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My API"
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          URL
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://api.example.com/health"
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          Check Interval (seconds)
        </label>
        <input
          type="number"
          value={interval}
          onChange={(e) => setInterval(e.target.value)}
          min="60"
          max="3600"
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition disabled:opacity-50"
        >
          {isLoading ? 'Adding...' : 'Add Target'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded transition"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
