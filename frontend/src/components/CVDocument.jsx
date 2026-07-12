// A no-LaTeX PDF of the tailored CV, built from the same structured `content`
// the backend renders LaTeX from. Styled to closely echo the Jake Gutierrez
// resume template: serif type, small-caps-style name, ruled section headers,
// tight bullet lists. Produces real vector text (selectable + ATS-parsable),
// not a rasterised screenshot, and renders entirely in the browser.
import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
} from '@react-pdf/renderer'

// Times mirrors the template's Computer Modern serif far better than the
// Helvetica default, with no external font files to bundle.
const styles = StyleSheet.create({
  page: {
    fontFamily: 'Times-Roman',
    fontSize: 10.5,
    lineHeight: 1.25,
    paddingTop: 34,
    paddingBottom: 34,
    paddingHorizontal: 42,
    color: '#000',
  },
  name: {
    fontFamily: 'Times-Bold',
    fontSize: 24,
    textAlign: 'center',
    letterSpacing: 1.5,
    textTransform: 'uppercase',
  },
  contact: {
    fontSize: 10,
    textAlign: 'center',
    marginTop: 4,
  },
  headline: {
    fontFamily: 'Times-Italic',
    fontSize: 10.5,
    textAlign: 'center',
    marginTop: 2,
  },
  section: {
    fontFamily: 'Times-Bold',
    fontSize: 13,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginTop: 12,
    marginBottom: 4,
    paddingBottom: 2,
    borderBottomWidth: 0.8,
    borderBottomColor: '#000',
  },
  summary: {
    marginBottom: 2,
  },
  project: {
    fontFamily: 'Times-Bold',
    marginTop: 5,
    marginBottom: 1,
  },
  eduRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  eduInstitution: { fontFamily: 'Times-Bold' },
  eduCredential: { fontFamily: 'Times-Italic', fontSize: 10 },
  eduMeta: { fontSize: 10, textAlign: 'right' },
  bulletRow: {
    flexDirection: 'row',
    marginBottom: 1.5,
    paddingLeft: 8,
  },
  bulletMark: {
    width: 10,
  },
  bulletText: {
    flex: 1,
  },
})

export default function CVDocument({ content }) {
  const c = content || {}
  const experience = Array.isArray(c.experience) ? c.experience : []
  const education = Array.isArray(c.education) ? c.education : []
  const sections = Array.isArray(c.sections) ? c.sections : []
  const skills = Array.isArray(c.skills) ? c.skills.filter(Boolean) : []

  return (
    <Document title={c.name ? `${c.name} — CV` : 'Tailored CV'}>
      <Page size="LETTER" style={styles.page}>
        <Text style={styles.name}>{c.name || 'Your Name'}</Text>
        {c.contact ? <Text style={styles.contact}>{c.contact}</Text> : null}
        {c.headline ? <Text style={styles.headline}>{c.headline}</Text> : null}

        {c.summary ? (
          <View>
            <Text style={styles.section}>Summary</Text>
            <Text style={styles.summary}>{c.summary}</Text>
          </View>
        ) : null}

        {education.length > 0 ? (
          <View>
            <Text style={styles.section}>Education</Text>
            {education.map((e, i) => {
              if (!e || (!e.institution && !e.credential)) return null
              return (
                <View key={i} wrap={false}>
                  <View style={styles.eduRow}>
                    <Text style={styles.eduInstitution}>{e.institution}</Text>
                    {e.location ? <Text style={styles.eduMeta}>{e.location}</Text> : null}
                  </View>
                  <View style={styles.eduRow}>
                    {e.credential ? (
                      <Text style={styles.eduCredential}>{e.credential}</Text>
                    ) : (
                      <Text />
                    )}
                    {e.date ? <Text style={styles.eduMeta}>{e.date}</Text> : null}
                  </View>
                </View>
              )
            })}
          </View>
        ) : null}

        {experience.length > 0 ? (
          <View>
            <Text style={styles.section}>Experience</Text>
            {experience.map((entry, i) => {
              const bullets = (entry.bullets || []).filter(Boolean)
              if (bullets.length === 0) return null
              return (
                <View key={i} wrap={false}>
                  {entry.project ? (
                    <Text style={styles.project}>{entry.project}</Text>
                  ) : null}
                  {bullets.map((b, j) => (
                    <View key={j} style={styles.bulletRow}>
                      <Text style={styles.bulletMark}>•</Text>
                      <Text style={styles.bulletText}>{b}</Text>
                    </View>
                  ))}
                </View>
              )
            })}
          </View>
        ) : null}

        {sections.map((s, i) => {
          const items = (s?.items || []).filter(Boolean)
          if (!s?.title || items.length === 0) return null
          return (
            <View key={i}>
              <Text style={styles.section}>{s.title}</Text>
              {items.map((it, j) => (
                <View key={j} style={styles.bulletRow}>
                  <Text style={styles.bulletMark}>•</Text>
                  <Text style={styles.bulletText}>{it}</Text>
                </View>
              ))}
            </View>
          )
        })}

        {skills.length > 0 ? (
          <View>
            <Text style={styles.section}>Technical Skills</Text>
            <Text>{skills.join(', ')}</Text>
          </View>
        ) : null}
      </Page>
    </Document>
  )
}
