import { useState } from 'react'
import { TargetDetail, Check, Group } from '../types'

interface TargetDetailViewProps {
  target: TargetDetail
  onDelete: (id: number) => void
  onManualCheck: (id: number) => void
  isDeleting: boolean
  isChecking: boolean
  groups: Group[]
  onGroupChange: (targetId: number, groupId: number | null) => void
  onPostmortem: (incidentId: number, note: string) => void
  isSavingPostmortem: boolean
}

export default function TargetDetailView({
  target,
  onDelete,
  onManualCheck,
  isDeleting,
  isChecking,
  groups,
  onGroupChange,
  onPostmortem,
  isSavingPostmortem,
}: TargetDetailViewProps) {
  const getStatusColor = (check: Check) => {
    return check.success
      ? 'bg-green-100 text-green-800'
      : 'bg-red-100 text-red-800'
  }

  const getStatusIcon = (check: Check) => {
    return check.success ? '✓' : '✗'
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Target Header */}
      <div className="mb-6 pb-6 border-b">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">{target.name}</h2>
        <p className="text-gray-600 break-all">{target.url}</p>
        <div className="text-sm text-gray-500 mt-2">
          Check interval: every {target.check_interval_seconds} seconds
        </div>
        <select value={target.group_id ?? ''} onChange={(e) => onGroupChange(target.id, e.target.value ? Number(e.target.value) : null)} className="mt-3 px-3 py-2 border rounded bg-white text-sm">
          <option value="">Ungrouped</option>
          {groups.map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}
        </select>
      </div>

      {/* Status Summary */}
      {target.recent_checks.length > 0 && (
        <div className="mb-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-gray-800">
                {target.recent_checks[0].success ? '🟢' : '🔴'}
              </div>
              <div className="text-sm text-gray-600">Current Status</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-600">
                {target.recent_checks[0].response_time_ms.toFixed(0)}ms
              </div>
              <div className="text-sm text-gray-600">Response Time</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-gray-800">
                {target.recent_checks[0].status_code}
              </div>
              <div className="text-sm text-gray-600">Status Code</div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 mb-6">
        <button
          onClick={() => onManualCheck(target.id)}
          disabled={isChecking}
          className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded transition disabled:opacity-50"
        >
          {isChecking ? 'Checking...' : 'Check Now'}
        </button>
        <button
          onClick={() => {
            if (window.confirm('Are you sure you want to delete this target?')) {
              onDelete(target.id)
            }
          }}
          disabled={isDeleting}
          className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded transition disabled:opacity-50"
        >
          {isDeleting ? 'Deleting...' : 'Delete'}
        </button>
      </div>

      {/* Recent Checks */}
      <div>
        <h3 className="text-xl font-bold text-gray-800 mb-4">Recent Checks</h3>
        {target.recent_checks.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No checks yet. Click "Check Now" to start monitoring.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Code
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Time
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Response Time
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">
                    Checked At
                  </th>
                </tr>
              </thead>
              <tbody>
                {target.recent_checks.map((check) => (
                  <tr
                    key={check.id}
                    className="border-b hover:bg-gray-50 transition"
                  >
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-3 py-1 rounded-full font-semibold text-sm ${getStatusColor(
                          check
                        )}`}
                      >
                        {getStatusIcon(check)} {check.success ? 'OK' : 'DOWN'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-800">
                      {check.status_code}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                        {check.response_time_ms.toFixed(0)}ms
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-600">
                      {new Date(check.checked_at).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 text-gray-600 text-xs">
                      {new Date(check.checked_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="mt-8">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Incident History</h3>
        {target.incidents.length === 0 ? <p className="text-gray-500">No incidents recorded.</p> : target.incidents.map((incident) => (
          <IncidentRow key={incident.id} incident={incident} onSave={onPostmortem} isSaving={isSavingPostmortem} />
        ))}
      </div>
    </div>
  )
}

function IncidentRow({ incident, onSave, isSaving }: { incident: TargetDetail['incidents'][number]; onSave: (id: number, note: string) => void; isSaving: boolean }) {
  const [editing, setEditing] = useState(false)
  const [note, setNote] = useState(incident.postmortem_note ?? '')
  return <div className="border rounded p-4 mb-3">
    <div className="flex justify-between text-sm text-gray-700">
      <span>{new Date(incident.started_at).toLocaleString()}</span>
      <span className={incident.status === 'resolved' ? 'text-green-700' : 'text-red-700'}>{incident.status}</span>
    </div>
    {incident.postmortem_note && !editing ? <div className="mt-3 bg-amber-50 p-3 text-sm"><span title="Documented">📝</span> {incident.postmortem_note} <button className="ml-2 text-blue-600" onClick={() => setEditing(true)}>Edit</button></div> : incident.status === 'resolved' && <div className="mt-3"><textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Postmortem note" className="w-full border rounded p-2 text-sm" rows={3} /><button disabled={isSaving || !note.trim()} onClick={() => { onSave(incident.id, note); setEditing(false) }} className="mt-2 bg-blue-500 text-white px-3 py-1 rounded text-sm">{isSaving ? 'Saving...' : incident.postmortem_note ? 'Save' : 'Add postmortem'}</button></div>}
  </div>
}
