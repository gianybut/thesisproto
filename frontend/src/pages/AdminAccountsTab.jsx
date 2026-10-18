import { useCallback, useEffect, useState } from 'react';
import { accountsAPI } from '../api';
import { errorMessage } from '../labels';
import { ROLE_LABELS } from '../roles';
import Icon from '../icons';
import ConfirmDialog from '../components/ConfirmDialog';
import Disclosure from '../components/Disclosure';
import EmptyState from '../components/EmptyState';
import ErrorSummary from '../components/ErrorSummary';
import Notice from '../components/Notice';
import SkeletonRows from '../components/SkeletonRows';

const MIN_PASSWORD = 8;   // backend routes/accounts.py MIN_PASSWORD

const ROLE_HINTS = {
  personnel: 'Records and uploads surveys, sees their own surveys, the damage map and damage records, and updates inspection status.',
  admin: 'Everything personnel can do, plus every survey, correcting and deleting damage records, accounts and the activity log.',
};

/** Field ids are prefixed so the error summary can link to them. */
const fid = (prefix, name) => `${prefix}-${name}`;

function Field({ prefix, name, label, hint, error, children }) {
  const id = fid(prefix, name);
  return (
    <div className={`field${error ? ' has-error' : ''}`}>
      <label className="field-label" htmlFor={id}>{label}</label>
      {hint && <p className="field-hint" id={`${id}-hint`}>{hint}</p>}
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
      {children(id, [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(' ') || undefined)}
    </div>
  );
}

function RoleChoice({ prefix, value, onChange, error, disabled }) {
  return (
    <fieldset className={`field${error ? ' has-error' : ''}`} id={fid(prefix, 'role')} tabIndex={-1}>
      <legend className="field-label">Role</legend>
      {error && <p className="field-error">{error}</p>}
      <div className="choice-list">
        {Object.entries(ROLE_LABELS).map(([role, label]) => (
          <label key={role} className="choice">
            <input type="radio" name={fid(prefix, 'role')} value={role} checked={value === role}
              disabled={disabled} onChange={() => onChange(role)} />
            <span>
              <span className="choice-label">{label}</span>
              <span className="field-hint">{ROLE_HINTS[role]}</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

const serverFieldErrors = (err) => err?.response?.data?.fields || {};

/** New account: name, username, role, first password, optional email. */
function CreateAccount({ onCreated, onCancel }) {
  const [form, setForm] = useState({ full_name: '', username: '', role: 'personnel', password: '', email: '' });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    const found = {};
    if (!form.full_name.trim()) found.full_name = 'Enter the person\'s full name';
    if (!form.username.trim()) found.username = 'Enter a username';
    if (form.password.length < MIN_PASSWORD) found.password = `The password must be at least ${MIN_PASSWORD} characters`;
    setErrors(found);
    setError('');
    if (Object.keys(found).length) return;
    setSaving(true);
    try {
      const res = await accountsAPI.create({ ...form, full_name: form.full_name.trim(), username: form.username.trim() });
      onCreated(res.data.account, res.data.message);
    } catch (err) {
      setErrors(serverFieldErrors(err));
      setError(Object.keys(serverFieldErrors(err)).length ? '' : errorMessage(err, 'Could not create the account. Try again.'));
      setSaving(false);
    }
  };

  const summary = Object.entries(errors).map(([k, message]) => ({ field: fid('new', k), message }));
  return (
    <form className="panel stack form-panel" onSubmit={submit} noValidate aria-labelledby="new-account-title">
      <h2 id="new-account-title" className="panel-title">Add an account</h2>
      <ErrorSummary errors={summary} />
      {error && <Notice kind="error">{error}</Notice>}
      <Field prefix="new" name="full_name" label="Full name" error={errors.full_name}>
        {(id, by) => <input id={id} className="input input-medium" value={form.full_name} onChange={set('full_name')} aria-describedby={by} autoComplete="off" />}
      </Field>
      <Field prefix="new" name="username" label="Username" hint="Used to sign in on the web app and the phone. Letters, numbers, dots, dashes or underscores; no spaces." error={errors.username}>
        {(id, by) => <input id={id} className="input input-medium" value={form.username} onChange={set('username')} aria-describedby={by} autoComplete="off" autoCapitalize="none" spellCheck={false} />}
      </Field>
      <RoleChoice prefix="new" value={form.role} onChange={(role) => setForm(f => ({ ...f, role }))} error={errors.role} />
      <Field prefix="new" name="password" label="First password" hint={`At least ${MIN_PASSWORD} characters. Give it to the person yourself, not by email or chat.`} error={errors.password}>
        {(id, by) => <input id={id} className="input input-medium" type="text" value={form.password} onChange={set('password')} aria-describedby={by} autoComplete="new-password" spellCheck={false} />}
      </Field>
      <Field prefix="new" name="email" label="Email (optional)" error={errors.email}>
        {(id, by) => <input id={id} className="input input-medium" type="email" value={form.email} onChange={set('email')} aria-describedby={by} autoComplete="off" />}
      </Field>
      <div className="inline-row">
        <button type="submit" className="btn btn-primary" disabled={saving}><Icon name="user-plus" />{saving ? 'Creating…' : 'Create account'}</button>
        <button type="button" className="btn btn-quiet" onClick={onCancel} disabled={saving}>Cancel</button>
      </div>
    </form>
  );
}

/** Change name and role of an existing account (role locked on your own). */
function EditAccount({ account, self, onSaved, onCancel }) {
  const prefix = `edit-${account.id}`;
  const [fullName, setFullName] = useState(account.full_name);
  const [role, setRole] = useState(account.role in ROLE_LABELS ? account.role : 'personnel');
  const [errors, setErrors] = useState({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!fullName.trim()) { setErrors({ full_name: 'Enter the person\'s full name' }); return; }
    setSaving(true);
    setErrors({});
    setError('');
    try {
      const res = await accountsAPI.update(account.id, self ? { full_name: fullName.trim() } : { full_name: fullName.trim(), role });
      onSaved(res.data.account, res.data.message);
    } catch (err) {
      setErrors(serverFieldErrors(err));
      setError(errorMessage(err, 'Could not save the changes. Try again.'));
      setSaving(false);
    }
  };

  return (
    <form className="account-form stack-sm" onSubmit={submit} noValidate
      onKeyDown={(e) => { if (e.key === 'Escape') { e.preventDefault(); onCancel(); } }}>
      {error && <Notice kind="error">{error}</Notice>}
      <Field prefix={prefix} name="full_name" label="Full name" error={errors.full_name}>
        {(id, by) => <input id={id} className="input input-medium" value={fullName} onChange={(e) => setFullName(e.target.value)} aria-describedby={by} autoFocus />}
      </Field>
      {self
        ? <p className="field-hint">You cannot change your own role. Another system administrator can.</p>
        : <RoleChoice prefix={prefix} value={role} onChange={setRole} error={errors.role} disabled={saving} />}
      <div className="inline-row">
        <button type="submit" className="btn btn-secondary" disabled={saving}>{saving ? 'Saving…' : 'Save changes'}</button>
        <button type="button" className="btn btn-quiet" onClick={onCancel} disabled={saving}>Cancel</button>
      </div>
    </form>
  );
}

function ResetPassword({ account, onDone, onCancel }) {
  const id = `password-${account.id}`;
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (password.length < MIN_PASSWORD) { setError(`The password must be at least ${MIN_PASSWORD} characters`); return; }
    setSaving(true);
    setError('');
    try {
      const res = await accountsAPI.resetPassword(account.id, password);
      onDone(res.data.message);
    } catch (err) {
      setError(errorMessage(err, 'Could not set the password. Try again.'));
      setSaving(false);
    }
  };

  return (
    <form className={`account-form field${error ? ' has-error' : ''}`} onSubmit={submit} noValidate
      onKeyDown={(e) => { if (e.key === 'Escape') { e.preventDefault(); onCancel(); } }}>
      <label className="field-label" htmlFor={id}>New password for {account.full_name}</label>
      <p className="field-hint" id={`${id}-hint`}>At least {MIN_PASSWORD} characters. Give it to them yourself. Their phone or browser stays signed in until that sign-in expires.</p>
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
      <div className="inline-row">
        <input id={id} className="input input-medium" type="text" value={password} autoFocus autoComplete="new-password" spellCheck={false}
          aria-describedby={`${id}-hint${error ? ` ${id}-error` : ''}`} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit" className="btn btn-secondary" disabled={saving}><Icon name="key" />{saving ? 'Saving…' : 'Set password'}</button>
        <button type="button" className="btn btn-quiet" onClick={onCancel} disabled={saving}>Cancel</button>
      </div>
    </form>
  );
}

function AccountStatus({ account }) {
  return account.account_status === 'active'
    ? <span className="status-label status-ready"><Icon name="check" size={16} />Active</span>
    : <span className="status-label status-waiting"><Icon name="power" size={16} />Turned off</span>;
}

export default function AdminAccountsTab({ user }) {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState(null);   // { id, mode: 'edit' | 'password' }
  const [toToggle, setToToggle] = useState(null);
  const [toggling, setToggling] = useState(false);

  const load = useCallback(() => accountsAPI.list()
    .then(res => { setAccounts(res.data.accounts); setError(''); })
    .catch(err => setError(errorMessage(err, 'Could not load the accounts. Check that the server is running, then reload the page.')))
    .finally(() => setLoading(false)), []);

  useEffect(() => { load(); }, [load]);

  const replace = (a) => setAccounts(prev => prev.map(x => (x.id === a.id ? a : x)));
  const done = (message) => { setNotice(message); setError(''); setEditing(null); };

  // Turning off asks first (toToggle opens the dialog); turning back on loses nothing, so it doesn't.
  const setStatus = async (a) => {
    const next = a.account_status === 'active' ? 'inactive' : 'active';
    setToggling(true);
    try {
      const res = await accountsAPI.update(a.id, { account_status: next });
      replace(res.data.account);
      setNotice(next === 'inactive'
        ? `Turned off ${a.full_name}'s account. They are signed out of the web app and the phone on their next action.`
        : `Turned ${a.full_name}'s account back on. They can sign in again.`);
      setError('');
    } catch (err) {
      setError(errorMessage(err, 'Could not change the account. Try again.'));
    } finally {
      setToggling(false);
      setToToggle(null);
    }
  };

  const active = accounts.filter(a => a.account_status === 'active');
  const admins = active.filter(a => a.role === 'admin').length;

  return (
    <div className="stack">
      <div className="inline-row admin-toolbar">
        <p className="muted num">
          {loading ? 'Loading accounts…' : <>{active.length} active · {admins} {admins === 1 ? 'administrator' : 'administrators'} · {accounts.length - active.length} turned off</>}
        </p>
        {!adding && (
          <button type="button" className="btn btn-primary" onClick={() => { setAdding(true); setNotice(''); }}>
            <Icon name="user-plus" />Add an account
          </button>
        )}
      </div>

      <div aria-live="polite">{notice && <Notice kind="success">{notice}</Notice>}</div>
      {error && <Notice kind="error">{error}</Notice>}

      {adding && (
        <CreateAccount
          onCancel={() => setAdding(false)}
          onCreated={(a, message) => { setAccounts(prev => [...prev, a].sort((x, y) => x.full_name.localeCompare(y.full_name))); setAdding(false); done(message); }}
        />
      )}

      {loading ? (
        <div className="panel"><SkeletonRows rows={4} label="Loading accounts" /></div>
      ) : accounts.length === 0 && !error ? (
        <EmptyState icon="user-circle" title="No accounts yet"
          action={<button type="button" className="btn btn-primary" onClick={() => setAdding(true)}><Icon name="user-plus" />Add an account</button>}>
          Add an account for each person who records or reviews surveys.
        </EmptyState>
      ) : (
        <ul className="panel account-list" aria-label="Accounts">
          {accounts.map(a => {
            const self = a.id === user.id;
            const mode = editing?.id === a.id ? editing.mode : null;
            return (
              <li key={a.id} className="account-row">
                <div className="account-main">
                  <p className="row-title">{a.full_name}{self && <span className="muted"> (you)</span>}</p>
                  <p className="survey-meta">{a.username}{a.email ? ` · ${a.email}` : ''}</p>
                </div>
                <div className="account-facts">
                  <span>{ROLE_LABELS[a.role] || ROLE_LABELS.personnel}</span>
                  <span className="survey-meta num">{a.survey_count} {a.survey_count === 1 ? 'survey' : 'surveys'}</span>
                </div>
                <div className="account-state"><AccountStatus account={a} /></div>
                <div className="survey-actions">
                  <Disclosure renderButton={(props) => (
                    <button className="btn btn-icon" aria-label={`More actions for ${a.full_name}`} {...props}><Icon name="dots" /></button>
                  )}>
                    {(close) => (
                      <ul className="menu-list">
                        <li><button type="button" className="menu-item" onClick={() => { close(); setNotice(''); setEditing({ id: a.id, mode: 'edit' }); }}>
                          <Icon name="pencil" />{self ? 'Change name' : 'Change name or role'}</button></li>
                        <li><button type="button" className="menu-item" onClick={() => { close(); setNotice(''); setEditing({ id: a.id, mode: 'password' }); }}>
                          <Icon name="key" />Set a new password</button></li>
                        {!self && (
                          <>
                            <li className="menu-divider" role="separator" />
                            <li><button type="button" className="menu-item" onClick={() => { close(); if (a.account_status === 'active') setToToggle(a); else setStatus(a); }}>
                              <Icon name="power" />{a.account_status === 'active' ? 'Turn off account' : 'Turn account back on'}</button></li>
                          </>
                        )}
                      </ul>
                    )}
                  </Disclosure>
                </div>
                {mode === 'edit' && (
                  <EditAccount account={a} self={self} onCancel={() => setEditing(null)}
                    onSaved={(u, message) => { replace(u); done(message); }} />
                )}
                {mode === 'password' && (
                  <ResetPassword account={a} onCancel={() => setEditing(null)} onDone={done} />
                )}
              </li>
            );
          })}
        </ul>
      )}

      <ConfirmDialog
        open={Boolean(toToggle)}
        title={toToggle ? `Turn off ${toToggle.full_name}'s account?` : ''}
        confirmLabel="Turn off account"
        cancelLabel="Keep it on"
        busyLabel="Turning off…"
        busy={toggling}
        onConfirm={() => setStatus(toToggle)}
        onCancel={() => setToToggle(null)}
      >
        <p>They can no longer sign in, and the web app and phone sign them out on their next action. Their surveys and records stay. You can turn the account back on later.</p>
      </ConfirmDialog>
    </div>
  );
}
