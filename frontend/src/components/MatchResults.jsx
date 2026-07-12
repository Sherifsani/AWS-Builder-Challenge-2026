// Render the /match response: ranked bullets (resolved against the bank), the
// missing-keywords gap analysis, and the suggested ordering.
export default function MatchResults({ result, bullets }) {
  if (!result) return null

  const byId = Object.fromEntries(bullets.map((b) => [b.bullet_id, b]))
  const { ranked_bullets = [], missing_keywords = [], suggested_order = [] } = result

  return (
    <div className="results">
      <div className="result-block">
        <h3>Ranked bullets</h3>
        {ranked_bullets.length === 0 ? (
          <p className="muted">No matches returned.</p>
        ) : (
          <ol className="ranked">
            {ranked_bullets.map((r) => {
              const b = byId[r.bullet_id]
              return (
                <li key={r.bullet_id}>
                  <p className="bullet-text">{b ? b.bullet : r.bullet_id}</p>
                  <p className="reason muted">{r.reason}</p>
                </li>
              )
            })}
          </ol>
        )}
      </div>

      <div className="result-block">
        <h3>Keyword gap</h3>
        {/* Signature: tailoring a resume is a diff between your bullets and the JD. */}
        <div className="keyword-diff">
          {missing_keywords.length === 0 ? (
            <>
              <div className="kd-head">Coverage</div>
              <div className="kd-line kd-ok">+ full coverage — no gaps found</div>
            </>
          ) : (
            <>
              <div className="kd-head">
                {missing_keywords.length} keyword{missing_keywords.length === 1 ? '' : 's'} missing from your bullets
              </div>
              {missing_keywords.map((k) => (
                <div className="kd-line kd-minus" key={k}>- {k}</div>
              ))}
            </>
          )}
        </div>
      </div>

      {suggested_order.length > 0 && (
        <div className="result-block">
          <h3>Suggested order</h3>
          <ol className="suggested">
            {suggested_order.map((id) => (
              <li key={id}>{byId[id] ? byId[id].bullet : id}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}
