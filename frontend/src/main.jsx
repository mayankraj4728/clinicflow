import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = '/api';

function App() {
  const [appointments, setAppointments] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    scheduled: 0,
    checkedIn: 0,
    completed: 0,
    cancelled: 0,
  });
  const [filter, setFilter] = useState('ALL');
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setError('');
      const [listRes, statsRes] = await Promise.all([
        fetch(`${API}/appointments`),
        fetch(`${API}/appointments/stats`),
      ]);
      if (!listRes.ok || !statsRes.ok) throw new Error('Backend unavailable');
      setAppointments(await listRes.json());
      setStats(await statsRes.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const visible =
    filter === 'ALL' ? appointments : appointments.filter((a) => a.status === filter);

  const advance = async (appointment) => {
    const next =
      appointment.status === 'SCHEDULED'
        ? 'CHECKED_IN'
        : appointment.status === 'CHECKED_IN'
        ? 'COMPLETED'
        : 'SCHEDULED';
    await fetch(`${API}/appointments/${appointment.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: next }),
    });
    load();
  };

  const remove = async (appointment) => {
    await fetch(`${API}/appointments/${appointment.id}`, { method: 'DELETE' });
    load();
  };

  const create = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await fetch(`${API}/appointments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_name: form.get('patient_name'),
        patient_email: form.get('patient_email'),
        doctor: form.get('doctor'),
        department: form.get('department'),
        appointment_type: form.get('appointment_type'),
        reason: form.get('reason'),
        status: 'SCHEDULED',
      }),
    });
    event.currentTarget.reset();
    setShowForm(false);
    load();
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">C</span>
          <div>
            <b>ClinicFlow</b>
            <small>DevOps Capstone</small>
          </div>
        </div>
        <nav>
          <a className="active">▦ <span>Dashboard</span></a>
          <a>✓ <span>Appointments</span></a>
          <a>◫ <span>Doctors</span></a>
          <a>◌ <span>Activity</span></a>
        </nav>
        <div className="side-bottom">
          <div className="upgrade">
            <strong>Care, on schedule.</strong>
            <p>Book, track and observe patient appointments in real time.</p>
          </div>
          <div className="profile">
            <div className="avatar">MR</div>
            <div>
              <b>Mayank Raj</b>
              <small>Developer</small>
            </div>
            <span>⋮</span>
          </div>
        </div>
      </aside>

      <main className="main">
        <header>
          <div>
            <p className="eyebrow">CLINIC / OVERVIEW</p>
            <h1>Good morning, Mayank 👋</h1>
            <p className="muted">Here's today's appointment schedule at a glance.</p>
          </div>
          <button className="primary" onClick={() => setShowForm(true)}>＋ New appointment</button>
        </header>

        {error && (
          <div className="alert">⚠ {error}. Start the backend and PostgreSQL, then refresh.</div>
        )}

        <section className="stats">
          <Stat label="Total appointments" value={stats.total} icon="▦" />
          <Stat label="Scheduled" value={stats.scheduled} icon="○" />
          <Stat label="Checked in" value={stats.checkedIn} icon="◔" />
          <Stat label="Completed" value={stats.completed} icon="✓" />
        </section>

        <section className="content-grid">
          <div className="panel appointments-panel">
            <div className="panel-head">
              <div>
                <h2>Appointments</h2>
                <p className="muted">Track patient visits across departments.</p>
              </div>
              <div className="filters">
                {['ALL', 'SCHEDULED', 'CHECKED_IN', 'COMPLETED', 'CANCELLED'].map((x) => (
                  <button
                    className={filter === x ? 'selected' : ''}
                    onClick={() => setFilter(x)}
                    key={x}
                  >
                    {x === 'ALL' ? 'All' : x.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
            {loading ? (
              <div className="empty">Loading appointments…</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Patient</th>
                      <th>Doctor</th>
                      <th>Department</th>
                      <th>Type</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((a) => (
                      <tr key={a.id}>
                        <td>
                          <div className="task-title">
                            <span className={`dot ${a.status.toLowerCase()}`}></span>
                            <div>
                              <b>{a.patient_name}</b>
                              <small>{a.reason}</small>
                            </div>
                          </div>
                        </td>
                        <td>{a.doctor}</td>
                        <td>{a.department}</td>
                        <td>
                          <span className={`priority ${a.appointment_type.toLowerCase()}`}>
                            {a.appointment_type.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <span className={`status ${a.status.toLowerCase()}`}>
                            {a.status.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <button className="icon-btn" onClick={() => advance(a)} title="Advance status">↻</button>
                          <button className="icon-btn" onClick={() => remove(a)} title="Delete appointment">✕</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!visible.length && <div className="empty">No appointments in this filter.</div>}
              </div>
            )}
          </div>

          <aside className="panel activity">
            <div className="panel-head">
              <div>
                <h2>Recent activity</h2>
                <p className="muted">Latest clinic events.</p>
              </div>
            </div>
            <Activity icon="✓" text="Monitoring dashboard completed" time="12 min ago" />
            <Activity icon="◔" text="Patient checked in at reception" time="38 min ago" />
            <Activity icon="＋" text="New appointment booked" time="1 hr ago" />
            <Activity icon="↗" text="Deployment pipeline passed" time="2 hrs ago" />
            <div className="pipeline">
              <span>CI</span><i></i><span>Build</span><i></i><span>Scan</span><i></i><span>Deploy</span>
            </div>
          </aside>
        </section>

        {showForm && (
          <div className="modal-backdrop">
            <form className="modal" onSubmit={create}>
              <div className="modal-head">
                <div>
                  <p className="eyebrow">NEW APPOINTMENT</p>
                  <h2>Book an appointment</h2>
                </div>
                <button type="button" className="close" onClick={() => setShowForm(false)}>×</button>
              </div>
              <label>Patient name<input name="patient_name" required placeholder="e.g. Aarav Sharma" /></label>
              <label>Patient email<input name="patient_email" type="email" placeholder="patient@example.com" /></label>
              <div className="form-row">
                <label>Doctor<input name="doctor" defaultValue="Dr. Meera Iyer" /></label>
                <label>Department
                  <select name="department">
                    <option>General Medicine</option>
                    <option>Cardiology</option>
                    <option>Dermatology</option>
                    <option>Orthopaedics</option>
                    <option>Paediatrics</option>
                  </select>
                </label>
              </div>
              <div className="form-row">
                <label>Type
                  <select name="appointment_type">
                    <option>CONSULTATION</option>
                    <option>FOLLOW_UP</option>
                    <option>EMERGENCY</option>
                    <option>SCREENING</option>
                  </select>
                </label>
                <label>Reason<input name="reason" placeholder="Routine check-up" /></label>
              </div>
              <button className="primary full">Book appointment</button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}

function Stat({ label, value, icon }) {
  return (
    <div className="stat">
      <div className="stat-icon">{icon}</div>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
        <span>Updated just now</span>
      </div>
    </div>
  );
}

function Activity({ icon, text, time }) {
  return (
    <div className="activity-row">
      <span className="activity-icon">{icon}</span>
      <div>
        <b>{text}</b>
        <small>{time}</small>
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
