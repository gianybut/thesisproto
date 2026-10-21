import { useState } from 'react';
import { detectionsAPI } from '../api';
import { damageName } from '../labels';
import Icon from '../icons';

// How much of the frame around the damage the close-up shows: the box times this, and never less
// than this share of the frame's width, so a hairline crack still has some road around it.
const CONTEXT = 2.5;
const MIN_SHARE = 0.2;
const ASPECT = 16 / 9;

/**
 * The part of a W x H frame to show for a damage box, at the preview's 16:9 shape:
 * { x, y, w, h } in frame pixels, centred on the box and kept inside the frame.
 */
function closeUpArea(bbox, W, H) {
  const bw = bbox.x2 - bbox.x1;
  const bh = bbox.y2 - bbox.y1;
  let w = Math.min(W, Math.max(bw * CONTEXT, bh * CONTEXT * ASPECT, W * MIN_SHARE));
  let h = w / ASPECT;
  if (h > H) { h = H; w = h * ASPECT; }
  const clamp = (v, max) => Math.max(0, Math.min(v, max));
  return {
    x: clamp((bbox.x1 + bbox.x2) / 2 - w / 2, W - w),
    y: clamp((bbox.y1 + bbox.y2) / 2 - h / 2, H - h),
    w, h,
  };
}

const hasBox = (b) => b && b.x2 > b.x1 && b.y2 > b.y1;

/** Style for the <img> that scales and shifts the picture so the close-up area fills its frame. */
function closeUpStyle(bbox, size) {
  const a = closeUpArea(bbox, size.w, size.h);
  return { width: `${(size.w / a.w) * 100}%`, left: `${(-a.x / a.w) * 100}%`, top: `${(-a.y / a.h) * 100}%` };
}

/**
 * A small close-up for a list row: the same zoom as DamagePreview, no controls. Pass `onClick` to
 * make it a button (it then needs `label`, said by screen readers); `selected` marks the open one.
 */
export function DamageThumb({ detection: d, onClick, label, selected }) {
  const [size, setSize] = useState(null);
  const [failed, setFailed] = useState(false);
  const src = detectionsAPI.imageUrl(d);
  const zoomed = hasBox(d.bbox) && size;
  const picture = (
    <span className="damage-thumb-frame">
      {src && !failed ? (
        <img
          src={src}
          alt=""
          loading="lazy"
          className={zoomed ? 'is-zoomed' : 'is-whole'}
          style={{ ...(zoomed ? closeUpStyle(d.bbox, size) : {}), visibility: size ? 'visible' : 'hidden' }}
          onLoad={(e) => setSize({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })}
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="damage-thumb-missing">No picture</span>
      )}
    </span>
  );
  if (!onClick) return <span className="damage-thumb">{picture}</span>;
  return (
    <button type="button" className={`damage-thumb${selected ? ' is-selected' : ''}`} onClick={onClick}
      aria-label={label} aria-expanded={Boolean(selected)}>
      {picture}
    </button>
  );
}

/**
 * A close-up of one damage: the frame it was found in (saved by the analysis, with its box drawn),
 * zoomed to the box, with a switch to the whole frame. A resident report has a photo and no box,
 * so it shows the whole photo. Give it key={detection.id} so the view resets per damage.
 *
 * title, onClose and children (facts, links) are the caller's: the survey page and the map show
 * different details around the same picture. Without a detection it keeps its size and shows
 * `placeholder`, so the layout around it does not move when a damage is chosen.
 */
export default function DamagePreview({ detection, title, onClose, placeholder, children }) {
  const [size, setSize] = useState(null);   // the picture's own pixels, known once it loads
  const [failed, setFailed] = useState(false);
  const [whole, setWhole] = useState(false);

  if (!detection) {
    return (
      <section className="damage-preview" aria-label="Close-up">
        <div className="damage-preview-head"><div className="damage-preview-title muted">{title}</div></div>
        <div className="damage-preview-frame"><p className="damage-preview-missing">{placeholder}</p></div>
        <div className="damage-preview-tools" />
      </section>
    );
  }

  const d = detection;
  const src = detectionsAPI.imageUrl(d);
  const canZoom = hasBox(d.bbox);
  const zoomed = canZoom && !whole && size;
  const name = damageName(d.damage_type);

  const imgStyle = zoomed ? closeUpStyle(d.bbox, size) : undefined;

  return (
    <section className="damage-preview" aria-label={`Picture of the ${name.toLowerCase()}`}>
      {(title || onClose) && (
        <div className="damage-preview-head">
          <div className="damage-preview-title">{title}</div>
          {onClose && (
            <button type="button" className="btn btn-quiet" onClick={onClose}><Icon name="x" />Close</button>
          )}
        </div>
      )}

      <div className="damage-preview-frame">
        {!src || failed ? (
          <p className="damage-preview-missing">
            {src ? 'The picture of this damage could not be loaded.' : 'No picture was saved for this damage.'}
          </p>
        ) : (
          <>
            {!size && <div className="damage-preview-loading skeleton" aria-hidden="true" />}
            <img
              src={src}
              alt={`${name}${d.timestamp_formatted && d.source_type !== 'public_report' ? ` at ${d.timestamp_formatted} in the video` : ''}${zoomed ? ', close-up' : ''}`}
              className={zoomed ? 'is-zoomed' : 'is-whole'}
              style={{ ...imgStyle, visibility: size ? 'visible' : 'hidden' }}
              onLoad={(e) => setSize({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })}
              onError={() => setFailed(true)}
            />
          </>
        )}
      </div>

      <div className="damage-preview-tools">
        {canZoom && size && !failed && (
          <button type="button" className="btn btn-quiet" onClick={() => setWhole(w => !w)}>
            <Icon name={whole ? 'search' : 'eye'} />{whole ? 'Zoom in on the damage' : 'Show the whole frame'}
          </button>
        )}
      </div>

      {children}
    </section>
  );
}
