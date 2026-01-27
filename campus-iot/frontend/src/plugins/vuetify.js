import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Custom dark theme - Cyberpunk inspired
const darkTheme = {
  dark: true,
  colors: {
    background: '#0a0a0f',
    surface: '#12121a',
    'surface-variant': '#1a1a25',
    primary: '#00ff9d',
    'primary-darken-1': '#00cc7d',
    secondary: '#ff006e',
    'secondary-darken-1': '#cc0058',
    accent: '#00d4ff',
    error: '#ff4757',
    info: '#00d4ff',
    success: '#00ff9d',
    warning: '#ffa502',
    'on-background': '#ffffff',
    'on-surface': '#e0e0e0',
  }
}

// Light theme - Clean & Modern
const lightTheme = {
  dark: false,
  colors: {
    background: '#f5f7fa',
    surface: '#ffffff',
    'surface-variant': '#f0f2f5',
    primary: '#00875a',
    'primary-darken-1': '#006644',
    secondary: '#d63384',
    'secondary-darken-1': '#ab296a',
    accent: '#0095ff',
    error: '#dc3545',
    info: '#0095ff',
    success: '#00875a',
    warning: '#fd7e14',
    'on-background': '#1a1a2e',
    'on-surface': '#333333',
  }
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: darkTheme,
      light: lightTheme
    }
  },
  defaults: {
    VCard: {
      elevation: 0,
      rounded: 'lg'
    },
    VBtn: {
      rounded: 'lg',
      fontWeight: 500
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable'
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable'
    }
  }
})
