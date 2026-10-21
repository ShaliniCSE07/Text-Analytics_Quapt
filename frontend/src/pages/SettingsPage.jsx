import React, { useEffect, useState } from 'react';
import PageHeader from '../components/PageHeader';
import { getTopics, addTopic, updateTopic, deleteTopic } from '../api/client';

export default function SettingsPage() {
  const [topics, setTopics] = useState({});
  const [loading, setLoading] = useState(true);
  
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  
  const [editingTopic, setEditingTopic] = useState(null);
  const [editDesc, setEditDesc] = useState('');

  const fetchTopics = async () => {
    setLoading(true);
    try {
      const data = await getTopics();
      setTopics(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopics();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newName.trim() || !newDesc.trim()) return;
    try {
      await addTopic(newName.trim(), newDesc.trim());
      setNewName('');
      setNewDesc('');
      await fetchTopics();
    } catch (err) {
      console.error(err);
      alert('Failed to add topic. It might already exist.');
    }
  };

  const handleEdit = (name, desc) => {
    setEditingTopic(name);
    setEditDesc(desc);
  };

  const handleSaveEdit = async (name) => {
    try {
      await updateTopic(name, editDesc.trim());
      setEditingTopic(null);
      await fetchTopics();
    } catch (err) {
      console.error(err);
      alert('Failed to update topic.');
    }
  };

  const handleDelete = async (name) => {
    if (window.confirm(`Are you sure you want to delete the topic "${name}"?`)) {
      try {
        await deleteTopic(name);
        await fetchTopics();
      } catch (err) {
        console.error(err);
        alert('Failed to delete topic.');
      }
    }
  };

  return (
    <div className="space-y-6 font-body text-textPrimary">
      <PageHeader
        title="Topic Settings"
        subtitle="Manage the taxonomy of topics used for review analysis"
      />

      <div className="bg-surface rounded-lg shadow-sm border border-gray-800/80 overflow-hidden">
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-lg font-bold font-display">Configured Topics</h2>
        </div>
        
        {loading ? (
          <div className="p-8 text-center text-textMuted animate-pulse">Loading topics...</div>
        ) : (
          <div className="divide-y divide-gray-800/60">
            {Object.entries(topics).map(([name, desc]) => (
              <div key={name} className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-bg/40 transition-colors">
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-textPrimary mb-1">{name}</div>
                  
                  {editingTopic === name ? (
                    <div className="flex items-center space-x-2 mt-2">
                      <input
                        type="text"
                        value={editDesc}
                        onChange={(e) => setEditDesc(e.target.value)}
                        className="flex-1 bg-bg border border-gray-700 rounded-md p-2 text-sm text-textPrimary focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
                      />
                      <button
                        onClick={() => handleSaveEdit(name)}
                        className="px-3 py-2 text-xs font-bold bg-amber text-bg rounded-md hover:bg-amber/90 transition-colors"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingTopic(null)}
                        className="px-3 py-2 text-xs font-medium text-textMuted hover:text-textPrimary transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="text-sm text-textMuted">{desc}</div>
                  )}
                </div>
                
                {editingTopic !== name && (
                  <div className="flex items-center space-x-3 flex-shrink-0">
                    <button
                      onClick={() => handleEdit(name, desc)}
                      className="px-3 py-1.5 text-xs font-medium text-amber border border-amber/40 bg-amber/5 rounded-md hover:bg-amber hover:text-bg transition-all"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(name)}
                      className="px-3 py-1.5 text-xs font-medium text-negative border border-negative/40 bg-negative/5 rounded-md hover:bg-negative hover:text-bg transition-all"
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            ))}
            
            {Object.keys(topics).length === 0 && (
              <div className="p-8 text-center text-textMuted">No topics configured.</div>
            )}
          </div>
        )}
      </div>

      <div className="bg-surface rounded-lg shadow-sm border border-gray-800/80 p-6">
        <h2 className="text-lg font-bold font-display mb-4">Add New Topic</h2>
        <form onSubmit={handleAdd} className="flex flex-col sm:flex-row items-start sm:items-end gap-4">
          <div className="flex-1 w-full">
            <label className="block text-xs font-medium text-textMuted mb-1 font-mono">Topic Name</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g. Claims - Settlement Speed"
              className="w-full bg-bg border border-gray-800 rounded-lg p-2.5 text-sm text-textPrimary placeholder:text-gray-600 focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
              required
            />
          </div>
          <div className="flex-[2] w-full">
            <label className="block text-xs font-medium text-textMuted mb-1 font-mono">Description / Keywords</label>
            <input
              type="text"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="e.g. claim settlement time, turnaround time, payout delay"
              className="w-full bg-bg border border-gray-800 rounded-lg p-2.5 text-sm text-textPrimary placeholder:text-gray-600 focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full sm:w-auto px-6 py-2.5 text-sm font-bold bg-amber text-bg rounded-lg hover:bg-amber/90 transition-colors h-[42px] flex items-center justify-center"
          >
            Add Topic
          </button>
        </form>
      </div>
    </div>
  );
}
