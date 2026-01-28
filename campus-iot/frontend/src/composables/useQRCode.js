import QRCode from 'qrcode'

/**
 * Composable for generating QR codes for rooms
 * Supports multiple formats and customization
 */
export function useQRCode() {
  
  /**
   * Generate a QR code as Data URL (base64)
   * @param {string} roomId - Room identifier
   * @param {object} options - QR code options
   * @returns {Promise<string>} Base64 data URL
   */
  async function generateQRDataURL(roomId, options = {}) {
    const url = getRoomURL(roomId)
    
    const defaultOptions = {
      width: 512,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#ffffff'
      },
      errorCorrectionLevel: 'H' // High error correction for better scanning
    }
    
    return await QRCode.toDataURL(url, { ...defaultOptions, ...options })
  }
  
  /**
   * Generate a QR code as SVG string
   * @param {string} roomId - Room identifier
   * @param {object} options - QR code options
   * @returns {Promise<string>} SVG string
   */
  async function generateQRSVG(roomId, options = {}) {
    const url = getRoomURL(roomId)
    
    const defaultOptions = {
      width: 256,
      margin: 1,
      color: {
        dark: '#000000',
        light: '#ffffff'
      }
    }
    
    return await QRCode.toString(url, { 
      ...defaultOptions, 
      ...options,
      type: 'svg'
    })
  }
  
  /**
   * Generate styled QR code with campus branding
   * @param {string} roomId - Room identifier
   * @param {string} theme - 'light' or 'dark'
   * @returns {Promise<string>} Base64 data URL
   */
  async function generateBrandedQR(roomId, theme = 'dark') {
    const colors = theme === 'dark' 
      ? { dark: '#00ff9d', light: '#1a1a2e' }
      : { dark: '#1a1a2e', light: '#ffffff' }
    
    return await generateQRDataURL(roomId, {
      width: 512,
      margin: 3,
      color: colors,
      errorCorrectionLevel: 'H'
    })
  }
  
  /**
   * Download QR code as PNG file
   * @param {string} roomId - Room identifier
   * @param {string} roomName - Room name for filename
   */
  async function downloadQRAsPNG(roomId, roomName = roomId) {
    const dataURL = await generateQRDataURL(roomId, { width: 1024 })
    
    const link = document.createElement('a')
    link.download = `QR_${roomName.replace(/\s+/g, '_')}.png`
    link.href = dataURL
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
  
  /**
   * Download QR code as SVG file
   * @param {string} roomId - Room identifier
   * @param {string} roomName - Room name for filename
   */
  async function downloadQRAsSVG(roomId, roomName = roomId) {
    const svg = await generateQRSVG(roomId)
    
    const blob = new Blob([svg], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.download = `QR_${roomName.replace(/\s+/g, '_')}.svg`
    link.href = url
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }
  
  /**
   * Generate printable PDF with QR code and room info
   * @param {string} roomId - Room identifier
   * @param {object} roomData - Room information
   */
  async function generatePrintablePDF(roomId, roomData) {
    const qrDataURL = await generateQRDataURL(roomId, { width: 400 })
    
    // Create printable HTML
    const printWindow = window.open('', '_blank')
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>QR Code - ${roomData.name}</title>
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&display=swap');
          
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Space Grotesk', sans-serif;
          }
          
          body {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: #f5f5f5;
          }
          
          .qr-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 400px;
          }
          
          .logo {
            font-size: 14px;
            color: #00ff9d;
            font-weight: 700;
            margin-bottom: 20px;
            letter-spacing: 2px;
          }
          
          .qr-image {
            width: 280px;
            height: 280px;
            margin: 20px auto;
            padding: 15px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
          }
          
          .room-id {
            font-size: 48px;
            font-weight: 700;
            color: #1a1a2e;
            margin: 20px 0 10px;
          }
          
          .room-name {
            font-size: 18px;
            color: #666;
            margin-bottom: 20px;
          }
          
          .floor {
            display: inline-block;
            background: #00ff9d;
            color: #1a1a2e;
            padding: 8px 24px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
          }
          
          .instructions {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px dashed #eee;
            font-size: 13px;
            color: #888;
          }
          
          .scan-icon {
            font-size: 24px;
            margin-bottom: 10px;
          }
          
          @media print {
            body { background: white; }
            .qr-card { box-shadow: none; }
          }
        </style>
      </head>
      <body>
        <div class="qr-card">
          <div class="logo">🏢 CAMPUS IOT - CESI NANCY</div>
          <img src="${qrDataURL}" class="qr-image" alt="QR Code ${roomId}">
          <div class="room-id">${roomId}</div>
          <div class="room-name">${roomData.name || 'Salle'}</div>
          <div class="floor">Étage ${roomData.floor || 'N/A'}</div>
          <div class="instructions">
            <div class="scan-icon">📱</div>
            Scannez ce QR code pour accéder aux<br>informations de la salle en temps réel
          </div>
        </div>
        <script>
          window.onload = () => window.print();
        </script>
      </body>
      </html>
    `)
    printWindow.document.close()
  }
  
  /**
   * Get the full URL for a room
   * @param {string} roomId - Room identifier
   * @returns {string} Full URL
   */
  function getRoomURL(roomId) {
    const baseURL = window.location.origin
    return `${baseURL}/room/${roomId}`
  }
  
  /**
   * Copy room URL to clipboard
   * @param {string} roomId - Room identifier
   * @returns {Promise<boolean>} Success status
   */
  async function copyRoomURL(roomId) {
    try {
      await navigator.clipboard.writeText(getRoomURL(roomId))
      return true
    } catch (err) {
      console.error('Failed to copy URL:', err)
      return false
    }
  }
  
  return {
    generateQRDataURL,
    generateQRSVG,
    generateBrandedQR,
    downloadQRAsPNG,
    downloadQRAsSVG,
    generatePrintablePDF,
    getRoomURL,
    copyRoomURL
  }
}
