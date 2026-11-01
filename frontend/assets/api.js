/* PlacePro - connects the pages to the Python backend (REST API). */
(() => {
const API = location.port === '8000' ? '/api' : 'http://127.0.0.1:8000/api';
const PAGE = (location.pathname.split('/').pop() || 'login.html').replace('.html', '');
const Q = new URLSearchParams(location.search);
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const fd = s => { if (!s) return '-'; const [d, t] = String(s).split(/[T ]/); const [y, m, dd] = d.split('-'); return `${dd}-${MON[m - 1]}-${y}` + (t ? ' ' + t.slice(0, 5) : ''); };
const GOOD = 'active open selected joined accepted eligible completed placed'.split(' '), WARN = 'shortlisted scheduled interview_scheduled interviewed on_hold pending offered draft rescheduled next_round'.split(' '),
  BAD = 'rejected closed no_show inactive not_eligible expired withdrawn cancelled blacklisted not_joined'.split(' ');
const badge = s => { if (!s) return '-'; const k = String(s).toLowerCase(); return `<span class="b ${GOOD.includes(k) ? 'g' : WARN.includes(k) ? 'a' : BAD.includes(k) ? 'r' : ''}">${esc(String(s).replace(/_/g, ' '))}</span>`; };
const money = v => v == null ? '-' : Number(v).toFixed(1);

function toast(msg, err) { const t = document.createElement('div'); t.className = 'toast' + (err ? ' err' : ''); t.textContent = msg; document.body.appendChild(t); setTimeout(() => t.remove(), 4500); }
async function call(method, path, body) {
  const h = { 'Content-Type': 'application/json' }, tk = localStorage.getItem('pp-token'); if (tk) h.Authorization = 'Bearer ' + tk;
  let r; try { r = await fetch(API + path, { method, headers: h, body: body ? JSON.stringify(body) : undefined }); }
  catch (e) { throw { message: 'Cannot reach the server. Is the backend running on port 8000?' }; }
  const j = await r.json().catch(() => ({}));
  if (r.status === 401 && PAGE !== 'login') { localStorage.removeItem('pp-token'); location.href = 'login.html'; throw { message: 'Session expired' }; }
  if (!r.ok) { const e = j.error || {}; throw { message: e.message || 'Request failed', details: e.details, status: r.status }; }
  return j;
}
const qs = o => { const p = new URLSearchParams(); Object.entries(o).forEach(([k, v]) => { if (v !== '' && v != null) p.set(k, v); }); const s = p.toString(); return s ? '?' + s : ''; };
const fail = (e, els) => { if (e.details && els && typeof e.details === 'object' && !Array.isArray(e.details)) Object.entries(e.details).forEach(([k, m]) => { const el = els[k]; if (el) { el.classList.add('bad'); el.parentNode.querySelector('.err').textContent = m; } }); toast(e.message || 'Something went wrong', true); };

/* ---- form helpers: fields are found by their label text, so the page design stays untouched ---- */
const norm = t => t.replace(/\(.*?\)/g, '').replace('*', '').trim().toLowerCase();
function formEls(root, map) { const o = {}; $$('label', root).forEach(l => { const k = map[norm(l.textContent)]; if (k) o[k] = l.parentNode.querySelector('input,select,textarea'); }); return o; }
function collect(els) {
  const o = {}; for (const [k, el] of Object.entries(els)) {
    if (el.multiple) o[k] = [...el.selectedOptions].map(x => x.value);
    else if (el.type === 'number' || el.type === 'date' || el.type === 'time' || el.tagName === 'SELECT') o[k] = el.value === '' ? null : (el.type === 'number' ? Number(el.value) : el.value);
    else o[k] = el.value.trim();
  } return o;
}
function fill(els, d) { for (const [k, el] of Object.entries(els)) { const v = d[k]; if (el.multiple) { const a = Array.isArray(v) ? v : []; [...el.options].forEach(o => o.selected = a.includes(o.value)); } else el.value = v == null ? '' : (el.type === 'date' ? String(v).slice(0, 10) : v); } }
const clearErr = root => { $$('.err', root).forEach(e => e.textContent = ''); $$('.bad', root).forEach(e => e.classList.remove('bad')); };
function opts(sel, items, val, txt, keep = true) { if (!sel) return; const cur = sel.value; sel.innerHTML = (keep && !sel.multiple ? '<option value="">Select</option>' : '') + items.map(i => `<option value="${esc(val(i))}">${esc(txt(i))}</option>`).join(''); if (cur) sel.value = cur; }
const byLabel = (root, text) => { const l = $$('label', root).find(x => norm(x.textContent) === text.toLowerCase()); return l && l.parentNode.querySelector('input,select,textarea'); };
const cardBy = title => $$('.card').find(c => { const h = $('h2', c); return h && h.textContent.trim().startsWith(title); });
function table(i, rows, actions) { const t = $$('table')[i]; if (!t) return; const head = $('tr', t).outerHTML; t.innerHTML = head + (rows.length ? rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}${actions ? `<td>${actions(r)}</td>` : ''}</tr>`).join('') : `<tr><td class="empty" colspan="20">No records found</td></tr>`); }
const tblIn = (card, heads, rows) => { if (!card) return; $('h2', card).insertAdjacentHTML('afterend', '<div class="tw"><table></table></div>'); const t = $('table', card); t.innerHTML = `<tr>${heads.map(h => `<th>${h}</th>`).join('')}</tr>` + (rows.length ? rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('') : '<tr><td class="empty" colspan="9">No data</td></tr>'); };
const fun = (card, rows) => { if (!card) return; const m = Math.max(1, ...rows.map(r => r.value)); const old = $('.fun,.tw', card); if (old) old.remove(); $('h2', card).insertAdjacentHTML('afterend', '<div class="fun">' + rows.map(r => `<div><span>${esc(r.label)}</span><i style="width:${r.value / m * 70}%"></i><b>${Number(r.value).toLocaleString()}</b></div>`).join('') + '</div>'); };
const kpis = vals => $$('.kpi b').forEach((b, i) => { if (vals[i] != null) b.textContent = Number(vals[i]).toLocaleString(); });
function filters(map, reload) {
  const card = cardBy('Filters'); if (!card) return () => ({}); const els = $$('input,select', card);
  const get = () => Object.fromEntries(map.map((k, i) => [k, els[i] ? els[i].value : '']));
  $$('button', card)[0].onclick = () => reload(get()); $$('button', card)[1].onclick = () => { els.forEach(e => e.value = ''); reload(get()); }; return { get, els };
}
let LK = null; const lookups = async () => LK || (LK = await call('GET', '/lookups'));
const cand = c => `${c.candidate_code} - ${c.full_name}`;

/* ---- shell: auth guard, header user, logout ---- */
const user = JSON.parse(localStorage.getItem('pp-user') || 'null');
if (PAGE !== 'login') {
  if (!localStorage.getItem('pp-token')) location.href = 'login.html';
  document.addEventListener('DOMContentLoaded', () => {
    if (user) { const b = $('.user b'); if (b) b.textContent = user.full_name; const s = $('.user small'); if (s) s.textContent = user.role.replace('_', ' '); const a = $('.av'); if (a) a.textContent = user.full_name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase(); }
    $$('a[href="login.html"]').forEach(a => a.addEventListener('click', () => { localStorage.removeItem('pp-token'); localStorage.removeItem('pp-user'); }));
  });
}

const P = {};
/* ---- LOGIN ---- */
const ROLE = { 'Admin': 'ADMIN', 'Recruiter': 'RECRUITER', 'Placement Officer': 'PLACEMENT_OFFICER' };
P.login = f => async () => {
  const [u, p] = $$('input', f), r = $('select', f);
  try { const d = await call('POST', '/auth/login', { username: u.value.trim(), password: p.value, role: ROLE[r.value] }); localStorage.setItem('pp-token', d.token); localStorage.setItem('pp-user', JSON.stringify(d.user)); location.href = 'dashboard.html'; }
  catch (e) { toast(e.message, true); }
};

/* ---- DASHBOARD ---- */
P.dashboard = async () => {
  const d = await call('GET', '/dashboard'), k = d.kpis;
  kpis([k.total_candidates, k.active_candidates, k.companies, k.open_jobs, k.applications, k.interviews, k.selected, k.placed]);
  $$('.kpi em').forEach(e => e.textContent = ''); $$('.kpi em')[3].textContent = 'Interviews today: ' + k.interviews_today;
  fun($$('.card')[$$('.card').findIndex(c => $('h2', c) && $('h2', c).textContent === 'Recruitment Funnel')], d.funnel);
  table(0, d.upcoming_interviews.map(i => [`INT-${i.interview_id}`, esc(i.candidate_name), esc(i.company_name), esc(i.round_type), fd(i.scheduled_date) + ' ' + (i.scheduled_time || ''), esc(i.mode), badge(i.status)]));
  table(1, d.recent_jobs.map(j => [esc(j.job_code), esc(j.job_title), esc(j.company_name), badge(j.status)]));
  table(2, d.recent_placements.map(p => [esc(p.candidate_name), esc(p.company_name), money(p.final_package_lpa) + ' LPA', badge(p.joining_status)]));
  table(3, d.recent_activity.map(a => [fd(a.logged_at), esc(a.user_name || 'System'), esc(a.module_name), esc(a.action_name), esc(a.description)]));
};

/* ---- CANDIDATES ---- */
const CMAP = { 'full name': 'full_name', email: 'email', mobile: 'mobile', 'date of birth': 'date_of_birth', gender: 'gender', qualification: 'qualification', college: 'college', university: 'university', 'passing year': 'passing_year', percentage: 'percentage', cgpa: 'cgpa', 'backlog count': 'backlog_count', 'primary technology': 'primary_technology', skills: 'skills', 'skill level': 'skill_level', 'years of experience': 'years_experience', 'current location': 'current_location', 'preferred location': 'preferred_location', 'profile status': 'profile_status' };
P.candidates = async () => {
  let page = 1, F = {};
  const load = async () => {
    const r = await call('GET', '/candidates' + qs({ ...F, page, page_size: 20 }));
    table(0, r.items.map(c => [esc(c.candidate_code), `<a href="candidate-details.html?id=${c.candidate_id}">${esc(c.full_name)}</a>`, esc(c.primary_technology || '-'), esc(c.qualification), c.passing_year, c.percentage ?? '-', c.backlog_count, badge(c.profile_status), badge(c.placement_status)]),
      row => { const id = r.items.find(c => c.candidate_code === row[0]).candidate_id; return `<a class="btn s" href="candidate-details.html?id=${id}">View</a> <a class="btn s" href="candidate-form.html?id=${id}">Edit</a> <button class="btn s" data-act="deact" data-id="${id}">Deactivate</button>`; });
    const pages = Math.max(1, Math.ceil(r.total / 20)); $('.pgn').innerHTML = `<button class="btn s" data-pg="-1">‹ Prev</button><button class="btn s p">${page} / ${pages}</button><button class="btn s" data-pg="1">Next ›</button>`;
    $('.pgn').onclick = e => { const b = e.target.closest('[data-pg]'); if (b) { page = Math.min(pages, Math.max(1, page + +b.dataset.pg)); load(); } };
  };
  filters(['candidate_code', 'name', 'mobile', 'email', 'primary_technology', 'passing_year', 'qualification', 'profile_status', 'placement_status'], v => { F = v; page = 1; load().catch(e => fail(e)); });
  P._act = async (a, id) => { if (a === 'deact' && confirm('Deactivate this candidate?')) { await call('PATCH', `/candidates/${id}/deactivate`); toast('Candidate deactivated'); load(); } };
  await load();
};
P['candidate-form'] = async () => {
  const f = $('form'), els = formEls(f, CMAP), id = Q.get('id'), lk = await lookups();
  opts(els.skills, lk.skills, s => s.skill_name, s => s.skill_name, false);
  if (id) { const c = await call('GET', '/candidates/' + id); c.skills_names = c.skills.map(s => s.skill_name); fill(els, { ...c, skills: c.skills_names, skill_level: (c.skills[0] || {}).proficiency_level, years_experience: (c.skills[0] || {}).years_experience }); $('h1').textContent = 'Edit Candidate'; byLabel(f, 'Candidate Code').value = c.candidate_code; }
  P._submit = async btn => {
    clearErr(f); const body = collect(els), upd = btn.textContent.trim() === 'Update';
    if (upd && !id) return toast('Open a candidate from the list (Edit) to update it.', true);
    try { const r = upd ? await call('PUT', '/candidates/' + id, body) : await call('POST', '/candidates', body); toast(`Candidate ${r.candidate_code} saved`); setTimeout(() => location.href = 'candidate-details.html?id=' + r.candidate_id, 700); } catch (e) { fail(e, els); }
  };
};
P['candidate-details'] = async () => {
  const c = await call('GET', '/candidates/' + Q.get('id')), set = (t, html) => { const k = cardBy(t); if (k) k.innerHTML = `<h2>${t}</h2>` + html; };
  $('.crumb').textContent = 'PlacePro / Candidates / ' + c.candidate_code; $('h1').textContent = 'Candidate Details';
  const ban = $$('.ban b'); [`${c.candidate_code} · ${c.full_name}`, `${c.profile_status} · ${c.placement_status}`, c.primary_technology || '-', c.applications.length, c.offers.length].forEach((v, i) => ban[i].textContent = v);
  const kv = d => '<div class="grid f">' + d.map(([k, v]) => `<div><label>${k}</label>${esc(v ?? '-')}</div>`).join('') + '</div>';
  set('Personal Information', kv([['Email', c.email], ['Mobile', c.mobile], ['DOB', fd(c.date_of_birth)], ['Gender', c.gender], ['Location', c.current_location]]));
  set('Academic Details', kv([['Qualification', c.qualification], ['College', c.college], ['University', c.university], ['Passing Year', c.passing_year], ['Percentage', c.percentage], ['Backlogs', c.backlog_count]]));
  set('Skills', c.skills.map(s => badge(s.skill_name).replace('b ', 'b v')).join(' ') || '<span class="help">No skills added</span>');
  const heads = a => '<tr>' + a.map(h => `<th>${h}</th>`).join('') + '</tr>', tb = (h, rows) => `<div class="tw"><table>${heads(h)}${rows.length ? rows.map(r => '<tr>' + r.map(x => `<td>${x}</td>`).join('') + '</tr>').join('') : '<tr><td class="empty" colspan="9">None yet</td></tr>'}</table></div>`;
  set('Applications History', tb(['Application', 'Job', 'Company', 'Eligibility', 'Status'], c.applications.map(a => [esc(a.application_code), esc(a.job_code + ' ' + a.job_title), esc(a.company_name), badge(a.eligibility_status), badge(a.application_status)])));
  set('Interview History', tb(['Application', 'Round', 'Date', 'Mode', 'Status'], c.interviews.map(i => [esc(i.application_code), `${i.round_number} - ${esc(i.round_type)}`, fd(i.scheduled_date), esc(i.mode), badge(i.status)])));
  set('Offer / Placement History', tb(['Offer', 'Designation', 'Package', 'Offer Status', 'Joining'], c.offers.map(o => [esc(o.offer_code), esc(o.designation), money(o.offered_package_lpa) + ' LPA', badge(o.offer_status), o.joining_status ? badge(o.joining_status) : '-'])));
  const ed = $$('a.btn').find(a => a.textContent.includes('Edit')); if (ed) ed.href = 'candidate-form.html?id=' + c.candidate_id;
};

/* ---- COMPANIES ---- */
const COMAP = { 'company name': 'company_name', industry: 'industry', website: 'website', location: 'location', 'hr name': 'hr_name', 'hr email': 'hr_email', 'hr mobile': 'hr_mobile', 'company type': 'company_type', status: 'status' };
P.companies = async () => {
  const f = $('form'), els = formEls(f, COMAP); let edit = null, rows = [];
  const load = async (F = {}) => { rows = await call('GET', '/companies' + qs(F));
    table(0, rows.map(c => [esc(c.company_code), esc(c.company_name), esc(c.industry || '-'), esc(c.location || '-'), esc(c.company_type || '-'), esc(c.hr_name || '-'), `<a href="jobs.html?company_id=${c.company_id}">${c.open_jobs} Open Jobs</a>`, badge(c.status)]),
      r => { const c = rows.find(x => x.company_code === r[0]); return `<button class="btn s" data-act="edit" data-id="${c.company_id}">Edit</button> <button class="btn s" data-act="${c.status === 'ACTIVE' ? 'inactive' : 'active'}" data-id="${c.company_id}">${c.status === 'ACTIVE' ? 'Set Inactive' : 'Activate'}</button>`; }); };
  filters(['name', 'industry', 'company_type', 'status'], v => load(v).catch(e => fail(e)));
  P._act = async (a, id) => { if (a === 'edit') { edit = id; fill(els, rows.find(c => c.company_id == id)); scrollTo(0, 0); toast('Editing company - change values and press Update'); }
    else { await call('PATCH', `/companies/${id}/status`, { status: a === 'inactive' ? 'INACTIVE' : 'ACTIVE' }); toast('Company status updated'); load(); } };
  P._submit = async btn => { clearErr(f); const body = collect(els), upd = btn.textContent.trim() === 'Update';
    if (upd && !edit) return toast('Press Edit on a company in the table first.', true);
    try { await (upd ? call('PUT', '/companies/' + edit, body) : call('POST', '/companies', body)); toast('Company saved'); f.reset(); edit = null; load(); } catch (e) { fail(e, els); } };
  await load();
};

/* ---- JOBS ---- */
const JMAP = { company: 'company_id', 'job code': 'job_code', 'job title': 'job_title', 'number of openings': 'openings', 'employment type': 'employment_type', location: 'location', 'minimum package': 'min_package_lpa', 'maximum package': 'max_package_lpa', qualification: 'qualifications', 'minimum percentage': 'min_percentage', 'minimum passing year': 'min_passing_year', 'maximum passing year': 'max_passing_year', 'maximum backlogs': 'max_backlogs', 'experience required': 'experience_min_years', 'required technology': 'required_technology', 'required skills': 'required_skills', 'minimum level': 'minimum_level', 'skill type': 'skill_type', 'posted date': 'posted_date', 'application deadline': 'application_deadline', status: 'status' };
P.jobs = async () => {
  const lk = await lookups(); let rows = [];
  const load = async (F = {}) => { const r = await call('GET', '/jobs' + qs({ ...F, page_size: 100 })); rows = r.items; const s = r.summary; kpis([s.open_jobs, s.total_openings, s.closing_this_week, s.draft]);
    table(0, rows.map(j => [esc(j.job_code), esc(j.company_name), esc(j.job_title), esc(j.employment_type), j.openings, esc(j.location), `${money(j.min_package_lpa)}-${money(j.max_package_lpa)}`, badge(j.status)]),
      r2 => { const j = rows.find(x => x.job_code === r2[0]); return `<a class="btn s" href="job-form.html?id=${j.job_id}">Edit</a> <a class="btn s" href="applications.html?job=${encodeURIComponent(j.job_code)}">View Applications</a> <button class="btn s" data-act="close" data-id="${j.job_id}">Close Job</button>`; }); };
  const fl = filters(['job_code', 'company_id', 'skill', 'location', 'status', 'employment_type'], v => load(v).catch(e => fail(e)));
  opts(fl.els[1], lk.companies, c => c.company_id, c => c.company_name); opts(fl.els[2], lk.skills, s => s.skill_name, s => s.skill_name);
  if (Q.get('company_id')) fl.els[1].value = Q.get('company_id');
  P._act = async (a, id) => { if (a === 'close' && confirm('Close this job?')) { await call('PATCH', `/jobs/${id}/close`); toast('Job closed'); load(fl.get()); } };
  await load(fl.get());
};
P['job-form'] = async () => {
  const f = $('form'), els = formEls(f, JMAP), id = Q.get('id'), lk = await lookups();
  opts(els.company_id, lk.companies, c => c.company_id, c => c.company_name); opts(els.required_technology, lk.skills, s => s.skill_name, s => s.skill_name); opts(els.required_skills, lk.skills, s => s.skill_name, s => s.skill_name, false);
  const cb = byLabel(f, 'Created By'); if (cb && user) cb.value = user.full_name + ' (logged-in user)';
  if (id) { const j = await call('GET', '/jobs/' + id), mand = j.skills.filter(s => s.mandatory_flag), tech = mand[0] ? mand[0].skill_name : null;
    fill(els, { ...j, qualifications: (j.qualification_rule || '').split('/'), required_technology: tech, required_skills: j.skills.filter(s => s.skill_name !== tech).map(s => s.skill_name), minimum_level: (j.skills[0] || {}).minimum_level, skill_type: j.skills.some(s => !s.mandatory_flag) ? 'Preferred' : 'Mandatory' });
    els.job_code.readOnly = true; $('h1').textContent = 'Edit Job'; }
  P._submit = async btn => { clearErr(f); const body = collect(els), upd = btn.textContent.includes('Update');
    if (upd && !id) return toast('Open a job from the list (Edit) to update it.', true);
    try { const r = upd ? await call('PUT', '/jobs/' + id, body) : await call('POST', '/jobs', body); toast('Job ' + r.job_code + ' saved'); setTimeout(() => location.href = 'jobs.html', 700); } catch (e) { fail(e, els); } };
};

/* ---- APPLICATIONS ---- */
P.applications = async () => {
  const lk = await lookups(), f = $('form'), AM = { candidate: 'candidate_id', job: 'job_id', source: 'source', 'assigned recruiter': 'assigned_recruiter_id' }, els = formEls(f, AM); let rows = [];
  opts(els.candidate_id, lk.candidates, c => c.candidate_id, cand); opts(els.job_id, lk.jobs, j => j.job_id, j => `${j.job_code} - ${j.job_title}`); opts(els.assigned_recruiter_id, lk.recruiters, u => u.user_id, u => u.full_name);
  const load = async (F = {}) => { const r = await call('GET', '/applications' + qs({ ...F, page_size: 100 })); rows = r.items;
    table(0, rows.map(a => [esc(a.application_code), `<a href="candidate-details.html?id=${a.candidate_id}">${esc(a.candidate_name)}</a>`, esc(a.company_name), esc(a.job_code), badge(a.eligibility_status) + (a.eligibility_status === 'NOT_ELIGIBLE' ? `<small class="rs">${esc(a.eligibility_reason)}</small>` : ''), badge(a.application_status), esc(a.recruiter_name || '-')]),
      r2 => { const a = rows.find(x => x.application_code === r2[0]); return `<button class="btn s" data-act="recheck" data-id="${a.application_id}">Check Eligibility</button> <button class="btn s" data-act="SHORTLISTED" data-id="${a.application_id}">Shortlist</button> <button class="btn s" data-act="REJECTED" data-id="${a.application_id}">Reject</button> <a class="btn s" href="interviews.html?app=${a.application_id}">Schedule Interview</a> <button class="btn s" data-act="history" data-id="${a.application_id}">History</button>`; }); };
  const f2 = await call('GET', '/reports/recruitment_funnel'); kpis([f2[0].value, f2[1].value, f2[2].value, f2[3].value]);
  const fl = filters(['application_code', 'candidate', 'company_id', 'job', 'status', 'eligibility', 'date_from', 'date_to'], v => load(v).catch(e => fail(e)));
  opts(fl.els[2], lk.companies, c => c.company_id, c => c.company_name); if (Q.get('job')) fl.els[3].value = Q.get('job');
  P._act = async (a, id) => {
    if (a === 'history') { const h = await call('GET', `/applications/${id}/history`), card = $('#h1'); card.style.display = 'block'; card.innerHTML = `<h2>Status History - ${esc(rows.find(x => x.application_id == id).application_code)}</h2><div class="tw"><table><tr><th>Old</th><th>New</th><th>Remarks</th><th>Changed By</th><th>Changed At</th></tr>${h.map(x => `<tr><td>${badge(x.old_status)}</td><td>${badge(x.new_status)}</td><td>${esc(x.remarks || '')}</td><td>${esc(x.changed_by)}</td><td>${fd(x.changed_at)}</td></tr>`).join('')}</table></div>`; return; }
    if (a === 'recheck') { const r = await call('POST', `/applications/${id}/recheck`); toast(r.status + ': ' + r.reason, r.status !== 'ELIGIBLE'); }
    else { const rem = a === 'REJECTED' ? prompt('Reason for rejection (optional):') : null; if (rem === null && a === 'REJECTED') return; await call('PATCH', `/applications/${id}/status`, { status: a, remarks: rem }); toast('Status changed to ' + a); }
    load(fl.get());
  };
  P._click = async b => { if (b.textContent.trim() !== 'Check Eligibility' || b.dataset.act) return false; const d = collect(els), box = $('#e1');
    if (!d.candidate_id || !d.job_id) { toast('Select a candidate and a job first.', true); return true; }
    try { const r = await call('POST', '/applications/eligibility/check', { candidate_id: +d.candidate_id, job_id: +d.job_id }); box.style.display = 'block'; box.classList.toggle('no', !r.eligible); box.innerHTML = `<b>${r.eligible ? 'ELIGIBLE' : 'NOT ELIGIBLE'}</b> - ${esc(r.reason)}`; } catch (e) { fail(e); } return true; };
  P._submit = async () => { clearErr(f); const d = collect(els); if (!d.candidate_id || !d.job_id) return toast('Select a candidate and a job.', true);
    try { const r = await call('POST', '/applications', { candidate_id: +d.candidate_id, job_id: +d.job_id, source: d.source, assigned_recruiter_id: d.assigned_recruiter_id ? +d.assigned_recruiter_id : null }); toast('Application ' + r.application_code + ' created'); load(fl.get()); } catch (e) { fail(e); } };
  await load(fl.get());
};

/* ---- INTERVIEWS ---- */
const IMAP = { application: 'application_id', 'round number': 'round_number', 'interview round': 'round_type', 'interview date': 'scheduled_date', 'interview time': 'scheduled_time', mode: 'mode', 'interviewer name': 'interviewer_name', 'meeting link / location': 'meeting_or_location' };
P.interviews = async () => {
  const lk = await lookups(), f = $('form'), els = formEls(f, IMAP); let rows = [];
  opts(els.application_id, lk.applications, a => a.application_id, a => `${a.application_code} - ${a.full_name} - ${a.job_code} (${a.application_status})`); if (Q.get('app')) els.application_id.value = Q.get('app');
  const load = async (F = {}) => { const r = await call('GET', '/interviews' + qs(F)); rows = r.items; const s = r.stats; kpis([s.today, s.this_week, s.completed, s.no_show]);
    table(0, rows.map(i => [`INT-${i.interview_id}`, esc(i.application_code), esc(i.candidate_name), esc(i.company_name), `${i.round_number} - ${esc(i.round_type)}`, fd(i.scheduled_date) + ' ' + (i.scheduled_time || ''), esc(i.mode), esc(i.interviewer_name || '-'), badge(i.status)]),
      r2 => { const i = rows.find(x => 'INT-' + x.interview_id === r2[0]); return `<button class="btn s" data-act="resched" data-id="${i.interview_id}">Reschedule</button> <a class="btn s" href="placement-process.html?app=${i.application_id}&interview=${i.interview_id}">Add Feedback</a> <button class="btn s" data-act="noshow" data-id="${i.interview_id}">Mark No Show</button>`; }); };
  const fl = filters(['candidate', 'company_id', 'status', 'date'], v => load(v).catch(e => fail(e))); opts(fl.els[1], lk.companies, c => c.company_id, c => c.company_name);
  P._act = async (a, id) => { if (a === 'resched') { const d = prompt('New date (YYYY-MM-DD):'); if (!d) return; await call('PATCH', `/interviews/${id}/reschedule`, { scheduled_date: d }); toast('Interview rescheduled'); }
    else if (confirm('Mark this candidate as No Show?')) { await call('PATCH', `/interviews/${id}/no-show`); toast('Marked as no show'); } load(fl.get()); };
  P._submit = async () => { clearErr(f); const d = collect(els); d.application_id = +d.application_id || null; try { await call('POST', '/interviews', d); toast('Interview scheduled'); f.reset(); load(fl.get()); } catch (e) { fail(e, els); } };
  await load(fl.get());
};

/* ---- PLACEMENT PROCESS (feedback -> offer -> joining) ---- */
P['placement-process'] = async () => {
  const lk = await lookups(), top = byLabel(document, 'Application'), S = { app: null, offer: null };
  const t1 = $('#t1'), t2 = $('#t2'), t3 = $('#t3');
  const E1 = formEls(t1, { 'interview round': 'interview_id', 'technical rating': 'technical_rating', 'communication rating': 'communication_rating', 'problem solving rating': 'problem_solving_rating', 'overall rating': 'overall_rating', 'interview result': 'recommendation', 'feedback remarks': 'remarks' });
  const E2 = formEls(t2, { designation: 'designation', 'offered package': 'offered_package_lpa', 'offer date': 'offer_date', 'expected joining date': 'expected_joining_date', 'offer status': 'offer_status', remarks: 'remarks' });
  const E3 = formEls(t3, { 'final designation': 'designation', 'final package': 'final_package_lpa', 'actual joining date': 'actual_joining_date', 'joining status': 'joining_status', 'placement status': 'placement_status' });
  opts(top, lk.applications, a => a.application_id, a => `${a.application_code} - ${a.full_name} - ${a.job_code} (${a.application_status})`);
  const loadApp = async id => {
    S.app = id ? await call('GET', '/applications/' + id) : null; S.offer = null; if (!S.app) return;
    const b = $$('.ban b'); [S.app.candidate_name, `${S.app.job_code} · ${S.app.job_title}`, S.app.company_name, S.app.application_status].forEach((v, i) => b[i].textContent = v);
    const iv = (await call('GET', '/interviews?application_id=' + id)).items; opts(E1.interview_id, iv, i => i.interview_id, i => `INT-${i.interview_id} - Round ${i.round_number} ${i.round_type} (${i.status})`); if (Q.get('interview')) E1.interview_id.value = Q.get('interview');
    try { S.offer = await call('GET', '/offers/by-application/' + id); fill(E2, { ...S.offer }); fill(E3, { designation: S.offer.designation, final_package_lpa: S.offer.offered_package_lpa, actual_joining_date: S.offer.actual_joining_date, joining_status: S.offer.joining_status, placement_status: S.offer.placement_status });
      byLabel(t2, 'Offer Code').value = S.offer.offer_code; byLabel(t3, 'Expected Joining Date').value = fd(S.offer.expected_joining_date); } catch (e) { if (e.status !== 404) throw e; byLabel(t2, 'Offer Code').value = '(auto-generated)'; }
    const vc = $$('a.btn').find(a => a.textContent.includes('View Candidate')); if (vc) vc.href = 'candidate-details.html?id=' + S.app.candidate_id;
  };
  top.onchange = () => loadApp(top.value).catch(e => fail(e)); if (Q.get('app')) { top.value = Q.get('app'); await loadApp(Q.get('app')); }
  P._submit = async (btn, form) => {
    if (!S.app) return toast('Select an application first.', true); clearErr(form); const t = btn.textContent.trim(); const E = form === t1 ? E1 : form === t2 ? E2 : E3;
    try {
      if (form === t1) { const d = collect(E1); if (!d.interview_id) return toast('Select the interview round.', true); await call('POST', `/interviews/${d.interview_id}/feedback`, d); toast('Feedback saved'); }
      else if (form === t2) { const d = collect(E2); if (t === 'Create Offer') { S.offer = await call('POST', '/offers', { ...d, application_id: +S.app.application_id }); toast('Offer ' + S.offer.offer_code + ' created'); }
        else { if (!S.offer) return toast('No offer exists yet.', true); S.offer = await call('PATCH', `/offers/${S.offer.offer_id}/status`, { status: d.offer_status, remarks: d.remarks }); toast('Offer status updated'); } }
      else { if (!S.offer) return toast('Create and accept an offer first.', true); const d = collect(E3); if (t === 'Mark Placed') { d.joining_status = 'JOINED'; d.placement_status = 'ACTIVE'; }
        await call('POST', `/offers/${S.offer.offer_id}/joining`, d); toast('Joining recorded'); }
      await loadApp(S.app.application_id);
    } catch (e) { fail(e, E); }
  };
};

/* ---- REPORTS ---- */
P.reports = async () => {
  const r = await call('GET', '/reports'), fu = r.recruitment_funnel, v = n => (fu.find(x => x.label.toLowerCase() === n) || {}).value || 0;
  kpis([v('applied'), v('interviewed'), v('selected'), v('joined')]); const kb = $$('.kpi b'); kb[4].textContent = (v('applied') ? (100 * v('joined') / v('applied')).toFixed(1) : '0.0') + '%'; kb[5].textContent = r.offer_to_joining.conversion_percent + '%';
  fun(cardBy('Recruitment Funnel'), fu); fun(cardBy('Applications by Status'), r.applications_by_status); fun(cardBy('Candidates by Technology'), r.candidates_by_technology); fun(cardBy('Open Jobs by Company'), r.open_jobs_by_company);
  fun(cardBy('Company-wise Placements'), r.company_placements); fun(cardBy('Technology-wise Placements'), r.technology_placements);
  const old = c => { const t = $('.tw', c); if (t) t.remove(); };
  [['Recruiter Performance', ['Recruiter', 'Applications', 'Selected', 'Joined'], r.recruiter_performance.map(x => [esc(x.recruiter), x.applications, x.selected, x.joined])],
   ['Pending Interviews', ['ID', 'Candidate', 'Date', 'Status'], r.pending_interviews.map(x => [`INT-${x.interview_id}`, esc(x.candidate), fd(x.scheduled_date), badge(x.status)])],
   ['Open Job Aging', ['Job', 'Posted', 'Days Open'], r.job_aging.map(x => [esc(x.job_code), fd(x.posted_date), x.days_open])],
   ['Placed / Unplaced', ['Candidate', 'Placement', 'Technology'], [...r.placed_candidates, ...r.unplaced_candidates].map(x => [esc(x.full_name), badge(x.placement_status), esc(x.primary_technology || '-')])]].forEach(([t, h, rows]) => { const c = cardBy(t); old(c); tblIn(c, h, rows); });
  const fc = cardBy('Filters'); if (fc) fc.style.display = 'none';
};

/* ---- ACTIVITY LOG ---- */
P['activity-log'] = async () => {
  const lk = await lookups(); const load = async (F = {}) => { const r = await call('GET', '/activity-logs' + qs(F)); table(0, r.map(l => [l.log_id, esc(l.user_name || 'System'), esc(l.module_name), esc(l.action_name), esc(l.record_id || '-'), esc(l.description || ''), fd(l.logged_at)])); };
  const fl = filters(['user_id', 'module', 'date'], v => load(v).catch(e => fail(e))); opts(fl.els[0], lk.users, u => u.user_id, u => u.full_name); await load();
};

/* ---- wiring ---- */
window.PP = { handle(form, btn) { if (PAGE === 'login') return P.login(form)(); return P._submit && P._submit(btn || form.querySelector('button'), form); } };
document.addEventListener('click', async e => {
  const b = e.target.closest('button,[data-act]'); if (!b) return;
  if (P._click && await P._click(b)) { e.stopPropagation(); return; }
  if (b.dataset.act && P._act) { try { await P._act(b.dataset.act, b.dataset.id); } catch (err) { fail(err); } }
}, true);
document.addEventListener('DOMContentLoaded', async () => {
  const run = P[PAGE]; if (!run || PAGE === 'login') return;
  try { await run(); } catch (e) { if (e.message !== 'Session expired') toast(e.message, true); }
});
})();
