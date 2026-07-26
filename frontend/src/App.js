import React, { useState } from 'react';
import './App.css';

function App() {
  const [major, setMajor] = useState('');
  const [completed, setCompleted] = useState('');
  const [userId, setUserId] = useState(null);
  const [eligibleCourses, setEligibleCourses] = useState([]);

  const handleCreateUser = async () => {
    const coursesArray = completed.split(',').map(c => c.trim());
    
    const response = await fetch('http://localhost:8000/users/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ major, completed_courses: coursesArray })
    });
    
    const data = await response.json();
    setUserId(data.user_id);
    fetchEligibleCourses(data.user_id);
  };

  const fetchEligibleCourses = async (id) => {
    const response = await fetch(`http://localhost:8000/users/${id}/eligible_courses`);
    const data = await response.json();
    setEligibleCourses(data);
  };

  const syncDatabase = async () => {
    await fetch('http://localhost:8000/admin/sync_department/COMPSCI', { method: 'POST' });
    alert("Database synced with mocked COMPSCI data. Click 'Find Classes' again.");
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', maxWidth: '800px', margin: 'auto' }}>
      <h1>Berkeley Class Scheduler</h1>
      
      <div style={{ marginBottom: '20px', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
        <h3>1. Setup Profile</h3>
        <input 
          placeholder="Major (e.g. Data Science)" 
          value={major} 
          onChange={e => setMajor(e.target.value)} 
          style={{ display: 'block', marginBottom: '10px', width: '100%', padding: '8px' }}
        />
        <input 
          placeholder="Completed Courses (comma separated, e.g. COMPSCI-61A, MATH-54)" 
          value={completed} 
          onChange={e => setCompleted(e.target.value)} 
          style={{ display: 'block', marginBottom: '10px', width: '100%', padding: '8px' }}
        />
        <button onClick={handleCreateUser} style={{ padding: '10px 20px', cursor: 'pointer' }}>
          Find Eligible Classes
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <button onClick={syncDatabase} style={{ padding: '8px 16px', backgroundColor: '#eee', border: '1px solid #ccc', cursor: 'pointer' }}>
          Run Scraper (Admin Sync)
        </button>
      </div>

      {userId && (
        <div>
          <h3>2. Classes You Can Take</h3>
          {eligibleCourses.length === 0 ? (
            <p>No eligible courses found. Try running the scraper sync first!</p>
          ) : (
            <ul style={{ listStyleType: 'none', padding: 0 }}>
              {eligibleCourses.map(course => (
                <li key={course.id} style={{ padding: '15px', border: '1px solid #ddd', marginBottom: '10px', borderRadius: '4px' }}>
                  <strong>{course.id}: {course.title}</strong>
                  <div style={{ marginTop: '8px', fontSize: '14px', color: '#555' }}>
                    <span style={{ display: 'inline-block', marginRight: '15px' }}>Status: {course.seat_status}</span>
                    <span>Prereqs: {course.prerequisites.join(', ') || 'None'}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

export default App;