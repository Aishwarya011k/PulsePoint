import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api'
import { Target, TargetDetail, Check, Group } from '../types'
import AddTargetForm from '../components/AddTargetForm'
import TargetDetailView from '../components/TargetDetailView'

interface DashboardPageProps {
  onLogout: () => void
}

export default function DashboardPage({ onLogout }: DashboardPageProps) {
  const [selectedTargetId, setSelectedTargetId] = useState<number | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [showGroupForm, setShowGroupForm] = useState(false)
  const [groupName, setGroupName] = useState('')
  const queryClient = useQueryClient()

  // Fetch targets
  const { data: targets = [], isLoading: targetsLoading } = useQuery({
    queryKey: ['targets'],
    queryFn: async () => {
      const response = await api.get<Target[]>('/targets')
      return response.data
    },
  })
  const { data: groups = [] } = useQuery({
    queryKey: ['groups'],
    queryFn: async () => (await api.get<Group[]>('/groups')).data,
  })

  // Fetch target details
  const { data: targetDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['target', selectedTargetId],
    queryFn: async () => {
      if (!selectedTargetId) return null
      const response = await api.get<TargetDetail>(
        `/targets/${selectedTargetId}`
      )
      return response.data
    },
    enabled: !!selectedTargetId,
  })

  // Add target mutation
  const addTargetMutation = useMutation({
    mutationFn: async (data: {
      name: string
      url: string
      check_interval_seconds: number
      group_id: number | null
    }) => {
      const response = await api.post<Target>('/targets', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['targets'] })
      setShowAddForm(false)
    },
  })

  const createGroupMutation = useMutation({
    mutationFn: async () => (await api.post<Group>('/groups', { name: groupName })).data,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['groups'] }); setGroupName(''); setShowGroupForm(false) },
  })
  const deleteGroupMutation = useMutation({
    mutationFn: async (id: number) => { await api.delete(`/groups/${id}`) },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['groups'] }); queryClient.invalidateQueries({ queryKey: ['targets'] }) },
  })
  const updateTargetMutation = useMutation({
    mutationFn: async ({ id, groupId }: { id: number; groupId: number | null }) => (await api.patch<Target>(`/targets/${id}`, { group_id: groupId })).data,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['targets'] }); queryClient.invalidateQueries({ queryKey: ['target', selectedTargetId] }) },
  })
  const postmortemMutation = useMutation({
    mutationFn: async ({ id, note }: { id: number; note: string }) => (await api.patch(`/incidents/${id}/postmortem`, { note })).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['target', selectedTargetId] }),
  })

  // Delete target mutation
  const deleteTargetMutation = useMutation({
    mutationFn: async (targetId: number) => {
      await api.delete(`/targets/${targetId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['targets'] })
      if (selectedTargetId === null) {
        setSelectedTargetId(null)
      }
    },
  })

  // Manual check mutation
  const manualCheckMutation = useMutation({
    mutationFn: async (targetId: number) => {
      const response = await api.post<Check>(
        `/targets/${targetId}/check-now`
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['target', selectedTargetId] })
      queryClient.invalidateQueries({ queryKey: ['targets'] })
    },
  })

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">PulsePoint</h1>
              <p className="text-gray-600">Monitor your uptime in real-time</p>
            </div>
            <button
              onClick={onLogout}
              className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Targets List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Targets</h2>
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded text-sm"
                >
                  + Add
                </button>
              </div>
              <div className="mb-4">
                <button onClick={() => setShowGroupForm(!showGroupForm)} className="text-sm text-blue-600">{showGroupForm ? 'Close group form' : '+ Manage groups'}</button>
                {showGroupForm && <form onSubmit={(e) => { e.preventDefault(); createGroupMutation.mutate() }} className="mt-2 flex gap-2"><input value={groupName} onChange={(e) => setGroupName(e.target.value)} required placeholder="Group name" className="min-w-0 flex-1 border rounded px-2 py-1 text-sm" /><button className="bg-gray-800 text-white rounded px-2 text-sm">Create</button></form>}
                {showGroupForm && groups.length > 0 && <div className="mt-2 space-y-1">{groups.map((group) => <div key={group.id} className="flex justify-between text-sm"><span>{group.name}</span><button onClick={() => deleteGroupMutation.mutate(group.id)} className="text-red-600">Delete</button></div>)}</div>}
              </div>

              {showAddForm && (
                <AddTargetForm
                  groups={groups}
                  onSubmit={(data) => addTargetMutation.mutate(data)}
                  onCancel={() => setShowAddForm(false)}
                  isLoading={addTargetMutation.isPending}
                />
              )}

              {targetsLoading ? (
                <div className="text-center py-4">Loading...</div>
              ) : targets.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No targets yet. Add one to get started!
                </div>
              ) : (
                <div className="space-y-4">
                  {[...groups.map((group) => ({ ...group, targets: targets.filter((target) => target.group_id === group.id) })), { id: 0, name: 'Ungrouped', color: null, targets: targets.filter((target) => !target.group_id) }].filter((section) => section.targets.length > 0).map((section) => (
                    <section key={section.id}>
                      <div className="flex items-center justify-between mb-2"><h3 className="font-semibold text-gray-700"><span className="inline-block w-2 h-2 rounded-full mr-2" style={{ backgroundColor: section.color ?? '#9ca3af' }} />{section.name}</h3><span className="text-xs text-gray-500">{section.targets.length} target{section.targets.length === 1 ? '' : 's'} · {(() => { const values = section.targets.map((target) => target.uptime_percentage).filter((value): value is number => value !== null); return values.length ? `${(values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1)}% uptime` : 'No uptime data' })()}</span></div>
                      <div className="space-y-2">
                  {section.targets.map((target) => (
                    <button
                      key={target.id}
                      onClick={() => setSelectedTargetId(target.id)}
                      className={`w-full text-left p-4 rounded-lg transition ${
                        selectedTargetId === target.id
                          ? 'bg-blue-100 border-2 border-blue-500'
                          : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      <h3 className="font-semibold text-gray-800">
                        {target.name}
                      </h3>
                      <p className="text-sm text-gray-600 truncate">
                        {target.url}
                      </p>
                    </button>
                  ))}
                      </div>
                    </section>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Target Details */}
          <div className="lg:col-span-2">
            {selectedTargetId === null ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                Select a target to view details
              </div>
            ) : detailLoading ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                Loading...
              </div>
            ) : targetDetail ? (
              <TargetDetailView
                target={targetDetail}
                onDelete={(id) => deleteTargetMutation.mutate(id)}
                onManualCheck={(id) => manualCheckMutation.mutate(id)}
                groups={groups}
                onGroupChange={(id, groupId) => updateTargetMutation.mutate({ id, groupId })}
                onPostmortem={(id, note) => postmortemMutation.mutate({ id, note })}
                isSavingPostmortem={postmortemMutation.isPending}
                isDeleting={deleteTargetMutation.isPending}
                isChecking={manualCheckMutation.isPending}
              />
            ) : null}
          </div>
        </div>
      </main>
    </div>
  )
}
