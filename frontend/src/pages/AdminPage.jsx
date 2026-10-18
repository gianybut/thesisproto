import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import AdminAccountsTab from './AdminAccountsTab';
import AdminActivityTab from './AdminActivityTab';

/**
 * Administration: the system administrator's own tasks (thesis Fig. 3.5.1 "Manage user
 * accounts" and "View system logs") as two tabs of one page, like the survey page.
 * Only an administrator reaches it (roles.js), and the server checks again on every call.
 */
export default function AdminPage({ tab, user }) {
  return (
    <div className="page">
      <PageHeader title="Administration">
        <nav className="tabs" aria-label="Administration sections">
          <Link to="/admin/accounts" className="tab" aria-current={tab === 'accounts' ? 'page' : undefined}>Accounts</Link>
          <Link to="/admin/activity" className="tab" aria-current={tab === 'activity' ? 'page' : undefined}>Activity log</Link>
        </nav>
      </PageHeader>
      {tab === 'activity' ? <AdminActivityTab /> : <AdminAccountsTab user={user} />}
    </div>
  );
}
