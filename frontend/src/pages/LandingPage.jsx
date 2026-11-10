import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../icons';
import { MAX_VIDEO_MINUTES } from '../labels';
import { SAMPLES_ONLY, serverAPI } from '../api';
import PublicHeader from '../components/PublicHeader';

// Thesis credits for the footer.
const TEAM = ['Kyle Cedric Panganiban', 'Janmikael Samson', 'Gian Paolo Ybut'];

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
  { code: 'D40', name: 'Pothole', text: 'A hole in the road surface.',
    img: '/landing/potholes-d40.jpg', alt: 'Four potholes, each outlined with a box labeled pothole' },
  { code: 'D00', name: 'Crack along the road', text: 'Runs in the same direction as traffic.',
    img: '/landing/longitudinal-crack-d00.jpg', alt: 'Two cracks running along a road, each outlined with a box labeled D00' },
  { code: 'D10', name: 'Crack across the road', text: 'Runs from side to side.',
    img: '/landing/transverse-crack-d10.jpg', alt: 'An asphalt road with a crack running across the lane, crossing the white lane line' },
  { code: 'D20', name: 'Alligator crack', text: 'Many connected cracks that look like scales.',
    img: '/landing/alligator-crack-d20.jpg', alt: 'A patch of connected, scale-like cracks outlined with a box labeled alligator crack' },
];

const MOBILE_FEATURES = [
  'Waits for a good location signal before you start recording.',
  `Keeps the screen on and stops on its own before the ${MAX_VIDEO_MINUTES}-minute limit.`,
  'Warns you if the location signal dropped during the drive.',
  'Uploads on Wi-Fi and retries by itself if the upload fails.',
];

const WEB_FEATURES = [
  { shot: 'upload page with progress', img: '/landing/upload-progress.jpg',
    alt: 'The upload page after sending a video: steps Uploaded, Analysing and Ready, with a progress bar at Analysing 5%', text: 'Upload a video and watch its progress.' },
  { shot: 'video with damage marked', img: '/landing/video-damage.jpg',
    alt: 'A survey of Maglabe Drive: the road video beside a list of 219 damages found, filterable by kind, with a pothole at 0:29 selected', text: 'Watch the video with each damage marked and labeled.' },
  { shot: 'damage map with routes', img: '/landing/damage-map.jpg',
    alt: 'The OcuLubak damage map: one drive through Palocpoc, with 219 damages pinned along the route in four colors by kind', text: 'See every damage on a map, with the route of each drive.' },
  { shot: 'placing a survey on the map', img: '/landing/place-on-map.jpg',
    alt: 'Placing a survey on the map: the road video paused at 2:13 beside a map with two numbered points joined by a line', text: 'No location track? Match a few spots in the video to the map and OcuLubak places the rest.' },
  { shot: 'damage list and download', img: '/landing/damage-records.jpg',
    alt: 'The damage records list: 234 records with filters by road name and kind, each row showing the damage, location, inspection status and confidence, and a Download menu offering CSV or JSON', text: 'Filter the list of damages and download it as a spreadsheet file (CSV) or JSON.' },
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

/**
 * A real image when `img` is given; otherwise a labelled grey box standing in for one.
 * To fill a placeholder, put the file in public/landing/ and pass img and alt.
 */
function Placeholder({ label, kind = 'Screenshot', className = '', img, alt, onOpen }) {
  if (img) {
    return (
      <button type="button" className="zoom" onClick={() => onOpen({ img, alt })} aria-label={`Enlarge image: ${alt}`}>
        <img src={img} alt="" className={`landing-img ${className}`} loading="lazy" />
      </button>
    );
  }
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
/** Large image preview in a native modal <dialog>. Escape, Close, or a click outside it closes it. */
function ImagePreview({ image, onClose }) {
  const ref = useRef();

  useEffect(() => {
    const d = ref.current;
    if (image && !d.open) d.showModal();
    if (!image && d.open) d.close();
  }, [image]);

  const closeOnOutsideClick = (e) => {
    const r = ref.current.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) ref.current.close();
  };

  return (
    <dialog ref={ref} className="preview" aria-label="Image preview" onClose={onClose} onClick={closeOnOutsideClick}>
      {image && (
        <figure>
          <img src={image.img} alt={image.alt} className="preview-img" />
          <figcaption className="preview-bar">
            <span>{image.alt}</span>
            <button type="button" className="btn btn-secondary" onClick={() => ref.current.close()}>
              <Icon name="x" />Close
            </button>
          </figcaption>
        </figure>
      )}
    </dialog>
  );
}

/**
 * Which detection model the server runs (ml/models/model_config.json, via GET /api/server/model):
 * signed-in users only, so the public website never asks for it.
 */
function ModelNote() {
  const [model, setModel] = useState(null);
  useEffect(() => {
    serverAPI.model().then(r => setModel(r.data)).catch(() => setModel(null));
  }, []);
  if (!model) return null;
  const deployed = model.deployed_at
    ? new Date(model.deployed_at).toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' })
    : null;
  return (
    <section id="model" className="landing-section landing-alt" aria-labelledby="model-title">
      <div className="landing-inner landing-narrow">
        <SectionHead id="model" title="The detection model" />
        <div className="card">
          <ul className="feature-list">
            <li><Icon name="check" className="feature-icon" />Model in use: <span className="code">{model.weights}</span>{model.run && <> (training run <span className="code">{model.run}</span>)</>}</li>
            {model.data_snapshot && <li><Icon name="check" className="feature-icon" />Trained on the labels saved in <span className="code">{model.data_snapshot}</span></li>}
            {deployed && <li><Icon name="check" className="feature-icon" />Put into service on {deployed}</li>}
            <li><Icon name="check" className="feature-icon" />Marks a damage when it is at least <span className="num">{Math.round(model.conf_threshold * 100)}%</span> sure</li>
          </ul>
          {model.stand_in && <p>This is a stand-in model, not the team’s own, used while the team’s model is being trained.</p>}
          {!model.stand_in && model.test_evaluated === false && (
            <p>Not yet checked on the held-out test drives: its accuracy figures so far come from the validation drives.</p>
          )}
        </div>
      </div>
    </section>
  );
}

export default function LandingPage({ user }) {
  const [preview, setPreview] = useState(null);
  // The public website has no accounts: its one button opens the sample surveys.
  const cta = SAMPLES_ONLY ? { to: '/samples', label: 'Try the sample surveys' }
    : user ? { to: '/', label: 'Open dashboard' } : { to: '/login', label: 'Log in' };

  return (
    <div className="landing" id="top">
      <a className="skip-link" href="#main">Skip to main content</a>

      <PublicHeader home="#top" cta={cta}
        links={SECTIONS.map(s => ({ href: `#${s.id}`, label: s.label }))} />

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
            <Placeholder img="/landing/damage-map.jpg" className="hero-img" onOpen={setPreview}
              alt="The OcuLubak damage map: one drive through Palocpoc, with 219 damages pinned along the route in four colors by kind" />
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
                  <Placeholder kind="Photo" label={d.name.toLowerCase()} img={d.img} alt={d.alt} className="placeholder-photo" onOpen={setPreview} />
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
            <Placeholder img="/landing/mobile-app-recording.jpg" className="phone-landscape" onOpen={setPreview}
              alt="The OcuLubak mobile app held sideways, ready to record: the camera view of a road with Horizon and Bonnet lines, GPS ±5 m, and a Start recording button" />
          </div>
        </section>

        <section id="web" className="landing-section" aria-labelledby="web-title">
          <div className="landing-inner">
            <SectionHead id="web" title="The web app" lead="Where your office reviews every drive." />
            <ul className="card-grid">
              {WEB_FEATURES.map(f => (
                <li key={f.text} className="card">
                  <Placeholder label={f.shot} img={f.img} alt={f.alt} className="placeholder-card" onOpen={setPreview} />
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

        {user && !SAMPLES_ONLY && <ModelNote />}
      </main>

      <ImagePreview image={preview} onClose={() => setPreview(null)} />

      <footer className="app-footer">
        <div className="footer-inner landing-footer">
          <p>
            <span className="footer-name">OcuLubak</span> is a thesis project of BS Computer Science students
            at De La Salle University-Dasmariñas.
          </p>
          <p>Team: {TEAM.join(', ')}</p>
        </div>
      </footer>
    </div>
  );
}
