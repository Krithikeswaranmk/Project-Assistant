export default function SkeletonLoader() {
  return (
    <div className="space-y-4">
      <div className="h-32 bg-gray-900 border border-gray-800 rounded-xl animate-pulse" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="h-48 bg-gray-900 border border-gray-800 rounded-xl animate-pulse" />
        <div className="h-48 bg-gray-900 border border-gray-800 rounded-xl animate-pulse" />
      </div>
      <div className="h-56 bg-gray-900 border border-gray-800 rounded-xl animate-pulse" />
    </div>
  )
}
