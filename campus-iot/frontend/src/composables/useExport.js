import { ref } from 'vue'

export function useExport() {
  const exporting = ref(false)

  // Export data to CSV
  function exportToCSV(data, filename = 'export') {
    if (!data || data.length === 0) {
      console.warn('No data to export')
      return
    }

    exporting.value = true

    try {
      // Get headers from first object
      const headers = Object.keys(data[0])
      
      // Create CSV content
      const csvContent = [
        headers.join(';'), // Header row
        ...data.map(row => 
          headers.map(header => {
            let value = row[header]
            // Handle special values
            if (value === null || value === undefined) value = ''
            if (typeof value === 'object') value = JSON.stringify(value)
            // Escape quotes and wrap in quotes if contains separator
            value = String(value).replace(/"/g, '""')
            if (value.includes(';') || value.includes('"') || value.includes('\n')) {
              value = `"${value}"`
            }
            return value
          }).join(';')
        )
      ].join('\n')

      // Add BOM for Excel compatibility
      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
      
      downloadBlob(blob, `${filename}_${formatDate()}.csv`)
    } finally {
      exporting.value = false
    }
  }

  // Export data to JSON
  function exportToJSON(data, filename = 'export') {
    exporting.value = true
    
    try {
      const jsonContent = JSON.stringify(data, null, 2)
      const blob = new Blob([jsonContent], { type: 'application/json' })
      downloadBlob(blob, `${filename}_${formatDate()}.json`)
    } finally {
      exporting.value = false
    }
  }

  // Export to PDF (simple text-based)
  function exportToPDF(title, data, columns) {
    exporting.value = true

    try {
      // Create a printable HTML document
      const printWindow = window.open('', '_blank')
      
      const tableRows = data.map(row => 
        `<tr>${columns.map(col => `<td>${row[col.key] ?? ''}</td>`).join('')}</tr>`
      ).join('')

      const html = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>${title}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #1e40af; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }
            .meta { color: #666; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #3b82f6; color: white; }
            tr:nth-child(even) { background: #f8fafc; }
            .footer { margin-top: 30px; color: #666; font-size: 12px; }
          </style>
        </head>
        <body>
          <h1>${title}</h1>
          <div class="meta">
            Exporté le ${new Date().toLocaleString('fr-FR')}<br>
            Total: ${data.length} enregistrements
          </div>
          <table>
            <thead>
              <tr>${columns.map(col => `<th>${col.title}</th>`).join('')}</tr>
            </thead>
            <tbody>
              ${tableRows}
            </tbody>
          </table>
          <div class="footer">
            Campus IoT - CESI Nancy - Bâtiment Orion
          </div>
        </body>
        </html>
      `

      printWindow.document.write(html)
      printWindow.document.close()
      printWindow.print()
    } finally {
      exporting.value = false
    }
  }

  // Export sensor data with formatting
  function exportSensorData(sensors, format = 'csv') {
    const data = sensors.map(sensor => ({
      id: sensor.id,
      nom: sensor.name,
      type: sensor.type,
      salle: sensor.room_id || 'Non assigné',
      valeur: sensor.latest_value,
      unite: sensor.unit,
      statut: sensor.status,
      derniere_maj: sensor.last_update
    }))

    if (format === 'csv') {
      exportToCSV(data, 'capteurs')
    } else if (format === 'json') {
      exportToJSON(data, 'capteurs')
    } else if (format === 'pdf') {
      exportToPDF('Liste des Capteurs', data, [
        { key: 'nom', title: 'Nom' },
        { key: 'type', title: 'Type' },
        { key: 'salle', title: 'Salle' },
        { key: 'valeur', title: 'Valeur' },
        { key: 'unite', title: 'Unité' },
        { key: 'statut', title: 'Statut' }
      ])
    }
  }

  // Export alerts
  function exportAlerts(alerts, format = 'csv') {
    const data = alerts.map(alert => ({
      id: alert.id,
      type: alert.type,
      message: alert.message,
      severite: alert.severity,
      capteur: alert.sensor_id,
      date: alert.created_at,
      resolu: alert.resolved ? 'Oui' : 'Non'
    }))

    if (format === 'csv') {
      exportToCSV(data, 'alertes')
    } else if (format === 'json') {
      exportToJSON(data, 'alertes')
    } else if (format === 'pdf') {
      exportToPDF('Historique des Alertes', data, [
        { key: 'date', title: 'Date' },
        { key: 'type', title: 'Type' },
        { key: 'message', title: 'Message' },
        { key: 'severite', title: 'Sévérité' },
        { key: 'resolu', title: 'Résolu' }
      ])
    }
  }

  // Export activity logs
  function exportActivityLogs(logs, format = 'csv') {
    const data = logs.map(log => ({
      date: log.timestamp,
      action: log.label || log.action,
      utilisateur: log.user_name || log.user_id,
      details: typeof log.details === 'object' ? JSON.stringify(log.details) : log.details
    }))

    if (format === 'csv') {
      exportToCSV(data, 'activite')
    } else if (format === 'json') {
      exportToJSON(data, 'activite')
    }
  }

  // Helper: Download blob
  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Helper: Format date for filename
  function formatDate() {
    return new Date().toISOString().slice(0, 10)
  }

  return {
    exporting,
    exportToCSV,
    exportToJSON,
    exportToPDF,
    exportSensorData,
    exportAlerts,
    exportActivityLogs
  }
}
