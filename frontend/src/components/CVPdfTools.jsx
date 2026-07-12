// The react-pdf machinery is ~1.4 MB, so it lives in its own module that
// CVView lazy-loads only after a CV has been generated. That keeps the heavy
// dependency out of the initial S3/CloudFront page load.
import { useState } from 'react'
import { PDFDownloadLink, PDFViewer } from '@react-pdf/renderer'
import CVDocument from './CVDocument'

export default function CVPdfTools({ content, filename }) {
  const [showPreview, setShowPreview] = useState(false)
  const pdfName = (filename || 'tailored-cv').replace(/\.tex$/, '.pdf')

  return (
    <>
      <div className="row-actions cv-toolbar">
        <button className="btn-primary" onClick={() => setShowPreview((v) => !v)}>
          {showPreview ? 'Hide preview' : 'Preview PDF'}
        </button>
        <PDFDownloadLink
          className="btn-secondary"
          document={<CVDocument content={content} />}
          fileName={pdfName}
        >
          {({ loading }) => (loading ? 'Preparing PDF…' : 'Download PDF')}
        </PDFDownloadLink>
      </div>
      {showPreview && (
        <PDFViewer className="pdf-preview" showToolbar={false}>
          <CVDocument content={content} />
        </PDFViewer>
      )}
    </>
  )
}
