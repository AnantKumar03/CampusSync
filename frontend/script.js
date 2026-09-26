
const API = location.port === '8000' ? '' : 'http://127.0.0.1:8000';
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const SLOTS = ['09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00'];
const ACTIVE = ['Pending', 'Accepted', 'Rescheduled'];

const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const qs = o => '?' + new URLSearchParams(o);

function toast(msg) {
  const t = $('toast'); t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2600);
}


async function api(path, method = 'GET', body) {
  try {
    const res = await fetch(API + path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined
    });
    return await res.json();
  } catch (e) {
    return { success: false, message: 'Cannot reach the server. Is server.py running?' };
  }
}
const list = x => (Array.isArray(x) ? x : []);  


let me = JSON.parse(sessionStorage.getItem('campus_user'));  
let ui = { fac: '', day: 'Mon', pick: null, resId: null };

$('loginForm').onsubmit = async e => {
  e.preventDefault();
  const res = await api('/api/login', 'POST', { email: $('email').value.trim(), password: $('password').value });
  if (!res.success) { $('authMsg').textContent = res.message; return; }
  me = { user_id: res.user_id, name: res.name, role: res.role };
  sessionStorage.setItem('campus_user', JSON.stringify(me));
  $('loginForm').reset(); $('authMsg').textContent = '';
  start();
};
$('logoutBtn').onclick = () => {
  sessionStorage.removeItem('campus_user'); me = null;
  ui = { fac: '', day: 'Mon', pick: null, resId: null };
  $('appView').hidden = true; $('authView').hidden = false; toast('You have been logged out');
};

function start() {
  $('authView').hidden = true; $('appView').hidden = false;
  $('userName').textContent = me.name; $('userRole').textContent = me.role;
  $('avatar').textContent = me.name[0].toUpperCase();
  render();
}
async function render() {
  const view = { Student: studentView, Faculty: facultyView, Admin: adminView }[me.role];
  $('content').innerHTML = await view();
}


async function studentView() {
  const facs = list(await api('/api/faculty'));
  if (!ui.fac && facs.length) ui.fac = String(facs[0].user_id);
  const [av, mine] = await Promise.all([
    api('/api/availability' + qs({ faculty_id: ui.fac })),
    api('/api/appointments' + qs({ student_id: me.user_id }))
  ]);
  const free = (av.slots || {})[ui.day] || [];
  return `
  <div class="card">
    <h2>Book a meeting with faculty</h2>
    <p class="muted small">Only times when the faculty has no class and no other meeting are shown.</p>
    <div class="grid2">
      <div><label for="fSel">Faculty</label>
        <select id="fSel" data-change="fac">${facs.map(f => `<option value="${f.user_id}" ${String(f.user_id) === ui.fac ? 'selected' : ''}>${esc(f.name)}</option>`).join('')}</select></div>
      <div><label for="dSel">Day</label>
        <select id="dSel" data-change="day">${DAYS.map(d => `<option ${d === ui.day ? 'selected' : ''}>${d}</option>`).join('')}</select></div>
    </div>
    <div class="slots">${free.map(t => `<button class="slot" data-act="pick" data-t="${t}" aria-pressed="${ui.pick === t}">${t}</button>`).join('') || '<p class="muted">No free slots on this day. Try another day.</p>'}</div>
    <label for="topic">Project / topic to discuss</label>
    <textarea id="topic" placeholder="e.g. Review of my ER diagram"></textarea>
    <button class="btn" data-act="book" ${ui.pick ? '' : 'disabled'}>${ui.pick ? `Request ${ui.day} ${ui.pick}` : 'Select a slot'}</button>
  </div>
  <div class="card"><h2>My bookings</h2>
    ${list(mine).map(a => `<div class="row"><div><strong>${esc(a.faculty)}</strong> · ${a.day} ${a.time_slot}
      <div class="muted small">${esc(a.topic)}</div></div>
      <div class="actions"><span class="tag ${a.status}">${a.status}</span>
      ${ACTIVE.includes(a.status) ? `<button class="btn ghost small" data-act="cancel" data-id="${a.appointment_id}">Cancel</button>` : ''}</div></div>`).join('')
      || '<p class="muted">You have no bookings yet.</p>'}
  </div>`;
}


async function facultyView() {
  const [appts, tt, av] = await Promise.all([
    api('/api/appointments' + qs({ faculty_id: me.user_id })),
    api('/api/timetable'),
    api('/api/availability' + qs({ faculty_id: me.user_id }))
  ]);
  const mine = list(appts), myTT = list(tt).filter(t => t.faculty_id === me.user_id);
  const pending = mine.filter(a => a.status === 'Pending');
  const others = mine.filter(a => a.status !== 'Pending');
  const options = DAYS.flatMap(d => ((av.slots || {})[d] || []).map(t => `<option value="${d}|${t}">${d} ${t}</option>`)).join('');

  const row = a => `<div class="row"><div><strong>${esc(a.student)}</strong> · ${a.day} ${a.time_slot}
      <div class="muted small">${esc(a.topic)}</div></div>
      <div class="actions">${a.status === 'Pending' ? `
        <button class="btn ok small" data-act="accept" data-id="${a.appointment_id}">Accept</button>
        <button class="btn bad small" data-act="reject" data-id="${a.appointment_id}">Reject</button>
        <button class="btn ghost small" data-act="resform" data-id="${a.appointment_id}">Reschedule</button>`
      : `<span class="tag ${a.status}">${a.status}</span>
         ${ACTIVE.includes(a.status) ? `<button class="btn ghost small" data-act="resform" data-id="${a.appointment_id}">Reschedule</button>` : ''}`}</div>
      ${ui.resId === a.appointment_id ? `<div class="actions" style="width:100%">
        <select id="resSel" aria-label="New time">${options || '<option value="">No free slots</option>'}</select>
        <button class="btn small" data-act="resok" data-id="${a.appointment_id}">Confirm new time</button></div>` : ''}</div>`;

  return `
  <div class="card"><h2>Booking requests (${pending.length})</h2>
    ${pending.map(row).join('') || '<p class="muted">No pending requests.</p>'}</div>
  <div class="card"><h2>My availability this week</h2>
    <p class="muted small">Classes come from the timetable set by the admin. Everything else is open for student bookings.</p>
    <div class="scroll"><table><thead><tr><th>Time</th>${DAYS.map(d => `<th>${d}</th>`).join('')}</tr></thead><tbody>
    ${SLOTS.map(t => `<tr><th>${t}</th>${DAYS.map(d => {
      const c = myTT.find(x => x.day === d && x.time_slot === t);
      if (c) return `<td class="class">${esc(c.subject)}<br>${esc(c.room)}</td>`;
      const b = mine.find(x => x.day === d && x.time_slot === t && ACTIVE.includes(x.status));
      return b ? `<td class="booked">${esc(b.student)}<br>${b.status}</td>` : '<td class="free">Free</td>';
    }).join('')}</tr>`).join('')}</tbody></table></div></div>
  <div class="card"><h2>All requests</h2>${others.map(row).join('') || '<p class="muted">Nothing here yet.</p>'}</div>`;
}


async function adminView() {
  const [tt, users, facs] = await Promise.all([
    api('/api/timetable'), api('/api/admin/users' + qs({ admin_id: me.user_id })), api('/api/faculty')
  ]);
  return `
  <div class="grid2">
    <div class="card"><h2>Add class to timetable</h2>
      <label for="tFac">Faculty</label><select id="tFac">${list(facs).map(f => `<option value="${f.user_id}">${esc(f.name)}</option>`).join('')}</select>
      <label for="tDay">Day</label><select id="tDay">${DAYS.map(d => `<option>${d}</option>`).join('')}</select>
      <label for="tSlot">Time</label><select id="tSlot">${SLOTS.map(t => `<option>${t}</option>`).join('')}</select>
      <label for="tSub">Subject</label><input id="tSub" type="text">
      <label for="tRoom">Room</label><input id="tRoom" type="text">
      <button class="btn" data-act="addClass">Add class</button></div>
    <div class="card"><h2>Add user</h2>
      <label for="uName">Name</label><input id="uName" type="text">
      <label for="uEmail">Email</label><input id="uEmail" type="email">
      <label for="uPass">Password</label><input id="uPass" type="text">
      <label for="uRole">Role</label><select id="uRole"><option>Faculty</option><option>Student</option></select>
      <button class="btn" data-act="addUser">Add user</button></div>
  </div>
  <div class="card"><h2>Timetable</h2>
    ${list(tt).map(t => `<div class="row"><div><strong>${esc(t.faculty)}</strong> · ${t.day} ${t.time_slot}
      <div class="muted small">${esc(t.subject)} · Room ${esc(t.room)}</div></div>
      <button class="btn ghost small" data-act="delClass" data-id="${t.timetable_id}">Remove</button></div>`).join('') || '<p class="muted">No classes yet.</p>'}</div>
  <div class="card"><h2>Users</h2>
    ${list(users.users).map(u => `<div class="row"><div><strong>${esc(u.name)}</strong><div class="muted small">${esc(u.email)}</div></div>
      <div class="actions"><span class="badge">${u.role}</span>
      <button class="btn ghost small" data-act="delUser" data-id="${u.user_id}">Remove</button></div></div>`).join('')}</div>`;
}


async function run(promise, okMsg) {
  const res = await promise;
  toast(res.success ? (okMsg || res.message) : res.message);
  if (res.success) { ui.pick = null; ui.resId = null; }
  render();
}

$('content').addEventListener('change', e => {
  if (e.target.dataset.change === 'fac') { ui.fac = e.target.value; ui.pick = null; render(); }
  if (e.target.dataset.change === 'day') { ui.day = e.target.value; ui.pick = null; render(); }
});

$('content').addEventListener('click', e => {
  const b = e.target.closest('button[data-act]'); if (!b) return;
  const act = b.dataset.act, id = Number(b.dataset.id), v = x => $(x).value.trim();

  if (act === 'pick') { ui.pick = ui.pick === b.dataset.t ? null : b.dataset.t; render(); }
  else if (act === 'book') {
    if (!v('topic')) return toast('Add a topic for the meeting');
    run(api('/api/appointments', 'POST', { student_id: me.user_id, faculty_id: Number(ui.fac), day: ui.day, time_slot: ui.pick, topic: v('topic') }));
  }
  else if (act === 'cancel') run(api('/api/appointments/cancel', 'POST', { appointment_id: id, user_id: me.user_id }));
  else if (act === 'accept') run(api('/api/appointments/respond', 'POST', { faculty_id: me.user_id, appointment_id: id, action: 'Accepted' }));
  else if (act === 'reject') run(api('/api/appointments/respond', 'POST', { faculty_id: me.user_id, appointment_id: id, action: 'Rejected' }));
  else if (act === 'resform') { ui.resId = ui.resId === id ? null : id; render(); }
  else if (act === 'resok') {
    const [day, time_slot] = ($('resSel').value || '|').split('|');
    if (!day) return toast('No free slots to move to');
    run(api('/api/appointments/reschedule', 'POST', { faculty_id: me.user_id, appointment_id: id, day, time_slot }));
  }
  else if (act === 'addClass') {
    run(api('/api/timetable', 'POST', { admin_id: me.user_id, faculty_id: Number($('tFac').value), day: $('tDay').value, time_slot: $('tSlot').value, subject: v('tSub'), room: v('tRoom') }));
  }
  else if (act === 'delClass') run(api('/api/timetable', 'DELETE', { admin_id: me.user_id, timetable_id: id }));
  else if (act === 'addUser') {
    run(api('/api/admin/users', 'POST', { admin_id: me.user_id, name: v('uName'), email: v('uEmail'), password: $('uPass').value, role: $('uRole').value }));
  }
  else if (act === 'delUser') run(api('/api/admin/users', 'DELETE', { admin_id: me.user_id, user_id: id }));
});

if (me) start();