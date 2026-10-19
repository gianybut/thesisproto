import { useEffect, useState } from 'react';
import { serverAPI } from '../api';
import Icon from '../icons';

const SHOW_KEY = 'phoneConnect.show';

const readShown = () => {
  try { return localStorage.getItem(SHOW_KEY) === '1'; } catch { return false; }
};

/**
 * "Connect a phone": the server address to type into the phone app's sign-in screen, read from
 * the backend (GET /api/server/info), because a browser cannot see its computer's network
 * address. Hidden until asked for, so it is not on screen during a presentation; the choice is
 * remembered in this browser only.
 */
export default function PhoneConnect() {
  const [info, setInfo] = useState(null);
  const [failed, setFailed] = useState(false);
  const [shown, setShown] = useState(readShown);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    serverAPI.info().then(res => setInfo(res.data)).catch(() => setFailed(true));
  }, []);

  const toggle = () => {
    const next = !shown;
    setShown(next);
    setCopied(false);
    try { localStorage.setItem(SHOW_KEY, next ? '1' : '0'); } catch { /* private window */ }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(info.address);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    } catch {
      setShown(true);   // clipboard blocked: at least show it so it can be read off
    }
  };

  return (
    <section className="panel phone-connect" aria-labelledby="phone-title">
      <h2 id="phone-title" className="panel-title"><Icon name="phone" className="shortcut-icon" />Connect a phone</h2>
      <p className="muted">
        On the phone&apos;s sign-in screen, enter this server address. The phone must be on the same Wi-Fi as this computer.
      </p>

      {failed ? (
        <p className="muted">Could not read the server address. Reload the page to try again.</p>
      ) : !info ? (
        <div className="skeleton server-address-loading" aria-label="Loading the server address" />
      ) : !info.address ? (
        <p>This computer is not connected to a network, so phones cannot reach it. Connect it to Wi-Fi, then reload this page.</p>
      ) : (
        <>
          <p className="server-address num" id="server-address" aria-live="polite">
            {shown
              ? info.address
              : <span aria-label="Server address hidden">{'•'.repeat(18)}</span>}
          </p>
          <div className="inline-row">
            <button type="button" className="btn btn-secondary" onClick={toggle} aria-controls="server-address" aria-pressed={shown}>
              <Icon name={shown ? 'eye-off' : 'eye'} />{shown ? 'Hide' : 'Show'}
            </button>
            <button type="button" className="btn btn-quiet" onClick={copy}>
              <Icon name={copied ? 'check' : 'copy'} />{copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          {shown && info.other_addresses?.length > 0 && (
            <p className="muted">
              If that one does not work: {info.other_addresses.map((a, i) => (
                <span key={a}>{i > 0 && ', '}<span className="num">{a}</span></span>
              ))}
            </p>
          )}
        </>
      )}
    </section>
  );
}
