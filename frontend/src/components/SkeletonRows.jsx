// §9: loading is skeleton rows at real row height, never a full-screen spinner.
export default function SkeletonRows({ rows = 5, label = 'Loading' }) {
  return (
    <div className="skeleton-list" aria-busy="true" aria-label={label}>
      {Array.from({ length: rows }, (_, i) => (
        <div className="skeleton-row" key={i}>
          <div className="skeleton" style={{ width: '6rem' }} />
          <div className="skeleton" style={{ flex: 1, maxWidth: '26rem' }} />
        </div>
      ))}
    </div>
  );
}
