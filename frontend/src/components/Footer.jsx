// The office that answers questions about the system (phone, email or room).
// Empty means the support line is not shown at all.
const SUPPORT_CONTACT = '';

export default function Footer() {
  return (
    <footer className="app-footer">
      <div className="footer-inner">
        <p><span className="footer-name">OcuLubak</span> · Road damage detection</p>
        {SUPPORT_CONTACT && <p className="footer-support">Support: {SUPPORT_CONTACT}</p>}
      </div>
    </footer>
  );
}
