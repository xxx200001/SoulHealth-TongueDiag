/**
 * 导出 HTML 结构为符合 MS Word 规范的 .doc/.docx 文件（可完美用 Microsoft Word / WPS 打开）
 */
export function exportToWord(filename, title, htmlContent) {
  const header = `
    <html xmlns:o='urn:schemas-microsoft-com:office:office' 
          xmlns:w='urn:schemas-microsoft-com:office:word' 
          xmlns='http://www.w3.org/TR/REC-html40'>
    <head>
      <meta charset='utf-8'>
      <title>${title}</title>
      <style>
        body { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; padding: 20pt; color: #1E293B; line-height: 1.6; }
        h1 { color: #2D5F4B; font-size: 22pt; text-align: center; border-bottom: 2pt solid #2D5F4B; padding-bottom: 10pt; margin-bottom: 20pt; }
        h2 { color: #A6402E; font-size: 14pt; margin-top: 18pt; margin-bottom: 8pt; border-left: 4pt solid #A6402E; padding-left: 8pt; }
        h3 { color: #2D5F4B; font-size: 12pt; margin-top: 12pt; }
        p { font-size: 11pt; margin-bottom: 8pt; }
        table { border-collapse: collapse; width: 100%; margin: 12pt 0; }
        th, td { border: 1pt solid #CBD5E1; padding: 7pt 10pt; font-size: 10.5pt; text-align: left; }
        th { background-color: #F1F5F9; color: #2D5F4B; font-weight: bold; }
        .meta-box { background-color: #F8F6F0; border: 1pt solid #C9A86C; padding: 12pt; margin-bottom: 15pt; border-radius: 4pt; }
        .badge { display: inline-block; padding: 2pt 6pt; background-color: #2D5F4B; color: white; font-size: 9pt; border-radius: 3pt; }
        .tag-danger { color: #D32F2F; font-weight: bold; }
        .footer-note { font-size: 9pt; color: #64748B; margin-top: 30pt; text-align: center; border-top: 1pt dashed #CBD5E1; padding-top: 10pt; }
      </style>
    </head>
    <body>
      <h1>${title}</h1>
      ${htmlContent}
      <div class="footer-note">本文档由 SOULHEALTH AI 中医辨证溯源平台自动生成 · 生成时间：${new Date().toLocaleString()}</div>
    </body>
    </html>
  `

  const blob = new Blob(['\ufeff' + header], { type: 'application/msword;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${filename}.doc`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * 触发标准高清 PDF 打印
 */
export function exportToPDF() {
  window.print()
}
