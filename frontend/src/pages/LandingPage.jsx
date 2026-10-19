import { Link } from 'react-router-dom';
import Icon from '../icons';
import { MAX_VIDEO_MINUTES } from '../labels';

// Thesis credits for the footer.
const TEAM = ['Kyle Cedric Panganiban', 'Janmikael Samson', 'Gian Paolo Ybut'];
const PARTNER_OFFICE = 'DPWH Cavite 2nd District Engineering Office';

const SECTIONS = [
  { id: 'how', label: 'How it works' },
  { id: 'mobile', label: 'Mobile app' },
  { id: 'web', label: 'Web app' },
  { id: 'faq', label: 'FAQ' },
];

const STEPS = [
  { icon: 'video', title: 'Record', text: 'Mount your phone on the windshield and drive.' },
  { icon: 'upload', title: 'Upload', text: 'Send the video and its location track.' },
  { icon: 'search', title: 'OcuLubak checks it', text: 'It goes through the video and marks road damage it finds.' },
  { icon: 'map', title: 'Review', text: 'See each damage on a map, check it in the video, and download the list.' },
];

const DAMAGE = [
  { code: 'D40', name: 'Pothole', text: 'A hole in the road surface.' },
  { code: 'D00', name: 'Crack along the road', text: 'Runs in the same direction as traffic.' },
  { code: 'D10', name: 'Crack across the road', text: 'Runs from side to side.' },
  { code: 'D20', name: 'Alligator crack', text: 'Many connected cracks that look like scales.' },
];

const MOBILE_FEATURES = [
  'Waits for a good location signal before you start recording.',
  `Keeps the screen on and stops on its own before the ${MAX_VIDEO_MINUTES}-minute limit.`,
  'Warns you if the location signal dropped during the drive.',
  'Uploads on Wi-Fi and retries by itself if the upload fails.',
];

const WEB_FEATURES = [
  { shot: 'upload page with progress', text: 'Upload a video and watch its progress.' },
  { shot: 'video with damage marked', text: 'Watch the video with each damage marked and labeled.' },
  { shot: 'damage map with routes', text: 'See every damage on a map, with the route of each drive.' },
  { shot: 'placing a survey on the map', text: 'No location track? Match a few spots in the video to the map and OcuLubak places the rest.' },
  { shot: 'damage list and download', text: 'Filter the list of damages and download it as a spreadsheet file (CSV) or JSON.' },
];

const AUDIENCES = [
  { title: 'Municipal engineers', text: 'See where damage is along each road before planning a site inspection.' },
  { title: 'Road maintenance crews', text: 'Know where to go: each damage is pinned on the map with the moment it appears in the video.' },
  { title: 'Planners and admin staff', text: 'Keep one list of damage and its repair stage, and download it for reports.' },
];

const FAQ = [
  { q: 'Does it replace inspection?', a: 'No. It helps you find and document damage faster, and a person still confirms it.' },
  { q: 'Does it work while driving?', a: 'No. You record first, then upload.' },
  { q: 'Does it record faces or plate numbers?', a: 'It only looks for road damage and doesn’t identify people or vehicles.' },
  { q: 'What happens to my videos?', a: 'Only authorized accounts can see them, and uploaded videos are deleted from the server after 30 days.' },
  { q: 'How long can a video be?', a: `Up to ${MAX_VIDEO_MINUTES} minutes and 500 MB.` },
];

/** Labelled grey box standing in for a real screenshot or photo until one is dropped in. */
function Placeholder({ label, kind = 'Screenshot', className = '' }) {
  return (
    <div className={`placeholder ${className}`} role="img" aria-label={`${kind} placeholder: ${label}`}>
      <span>{kind}: {label}</span>
    </div>
  );
}

function SectionHead({ id, title, lead }) {
  return (
    <div className="landing-section-head">
      <h2 id={`${id}-title`}>{title}</h2>
      {lead && <p className="landing-lead">{lead}</p>}
    </div>
  );
}

/** Public page explaining OcuLubak. "/" for visitors, "/about" for everyone. */
export default function LandingPage({ user }) {
  const cta = user ? { to: '/', label: 'Open dashboard' } : { to: '/login', label: 'Log in' };

  return (
    <div className="landing" id="top">
      <a className="skip-link" href="#main">Skip to main content</a>

      <header className="landing-header">
        <div className="landing-bar">
          <a href="#top" className="brand">
            <img src="/oculubak-icon-mono.svg" alt="" width="44" height="28" />
            <span className="brand-name">OcuLubak</span>
          </a>
          <nav className="landing-nav" aria-label="On this page">
            <ul>
              {SECTIONS.map(s => <li key={s.id}><a href={`#${s.id}`}>{s.label}</a></li>)}
            </ul>
          </nav>
          <Link to={cta.to} className="btn btn-primary landing-cta">{cta.label}</Link>
        </div>
      </header>

      <main id="main" tabIndex={-1}>
        <section className="landing-section hero" aria-labelledby="hero-title">
          <div className="landing-inner hero-grid">
            <div className="hero-text">
              <h1 id="hero-title">Find road damage from a single drive.</h1>
              <p className="landing-lead">
                Record a drive with your phone, upload the video, and OcuLubak finds potholes and cracks
                and pins each one on a map.
              </p>
              <div className="hero-actions">
                <Link to={cta.to} className="btn btn-primary">{cta.label}</Link>
                <a href="#how" className="btn btn-secondary">See how it works<Icon name="chevron-down" size={16} /></a>
              </div>
            </div>
            <Placeholder label="the damage map with pinned potholes and cracks" className="placeholder-wide" />
          </div>
        </section>

        <section id="how" className="landing-section landing-alt" aria-labelledby="how-title">
          <div className="landing-inner">
            <SectionHead id="how" title="How it works" />
            <ol className="steps">
              {STEPS.map((s, i) => (
                <li key={s.title} className="card step">
                  <div className="step-top">
                    <span className="step-number num" aria-hidden="true">{i + 1}</span>
                    <Icon name={s.icon} size={24} className="step-icon" />
                  </div>
                  <h3><span className="visually-hidden">Step {i + 1}: </span>{s.title}</h3>
                  <p>{s.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="find" className="landing-section" aria-labelledby="find-title">
          <div className="landing-inner">
            <SectionHead id="find" title="What it can find" lead="OcuLubak looks for four kinds of road damage." />
            <ul className="card-grid">
              {DAMAGE.map(d => (
                <li key={d.code} className="card damage-card">
                  <Placeholder kind="Photo" label={d.name.toLowerCase()} className="placeholder-photo" />
                  <h3>{d.name}</h3>
                  <p>{d.text}</p>
                  <p className="code">Technical name: {d.code}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section id="mobile" className="landing-section landing-alt" aria-labelledby="mobile-title">
          <div className="landing-inner split">
            <div>
              <SectionHead id="mobile" title="The mobile app"
                lead="Records the video and the location track together on one phone, then sends both to OcuLubak." />
              <ul className="feature-list">
                {MOBILE_FEATURES.map(f => <li key={f}><Icon name="check" className="feature-icon" />{f}</li>)}
              </ul>
            </div>
            <Placeholder label="the mobile app while recording" className="placeholder-phone" />
          </div>
        </section>

        <section id="web" className="landing-section" aria-labelledby="web-title">
          <div className="landing-inner">
            <SectionHead id="web" title="The web app" lead="Where your office reviews every drive." />
            <ul className="card-grid">
              {WEB_FEATURES.map(f => (
                <li key={f.text} className="card">
                  <Placeholder label={f.shot} className="placeholder-card" />
                  <p>{f.text}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section id="who" className="landing-section landing-alt" aria-labelledby="who-title">
          <div className="landing-inner">
            <SectionHead id="who" title="Who it’s for" />
            <ul className="card-grid card-grid-3">
              {AUDIENCES.map(a => (
                <li key={a.title} className="card">
                  <h3>{a.title}</h3>
                  <p>{a.text}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section id="faq" className="landing-section" aria-labelledby="faq-title">
          <div className="landing-inner landing-narrow">
            <SectionHead id="faq" title="Good to know" />
            <div className="faq">
              {FAQ.map(f => (
                <details key={f.q} className="details">
                  <summary>{f.q}</summary>
                  <p className="details-body">{f.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <div className="footer-inner landing-footer">
          <p>
            <span className="footer-name">OcuLubak</span> is a thesis project of BS Computer Science students
            at De La Salle University-Dasmariñas.
          </p>
          <p>Team: {TEAM.join(', ')}</p>
          <p>Partner office: {PARTNER_OFFICE}</p>
        </div>
      </footer>
    </div>
  );
}
