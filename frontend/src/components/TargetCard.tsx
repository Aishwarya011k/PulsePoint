import { Target } from '../types'

interface TargetCardProps {
  target: Target
  isSelected: boolean
  onClick: () => void
}

export default function TargetCard({
  target,
  isSelected,
  onClick,
}: TargetCardProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-lg transition border-2 ${
        isSelected
          ? 'bg-blue-50 border-blue-500'
          : 'bg-white border-gray-200 hover:border-gray-300'
      }`}
    >
      <h3 className="font-semibold text-gray-800">{target.name}</h3>
      <p className="text-sm text-gray-600 truncate">{target.url}</p>
      <div className="text-xs text-gray-500 mt-2">
        Check every {target.check_interval_seconds}s
      </div>
    </button>
  )
}
