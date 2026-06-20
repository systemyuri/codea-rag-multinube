import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1e3a8a', // azul profundo (confianza, legal)
    },
    secondary: {
      main: '#f59e0b', // ámbar (calidez, atención)
    },
    background: {
      default: '#f8fafc', // gris muy claro
    },
  },
  typography: {
    fontFamily: '"Segoe UI", "Roboto", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    body1: {
      fontSize: '1rem',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 28, // botones redondeados
          textTransform: 'none', // evitar mayúsculas automáticas
        },
      },
    },
  },
});

export default theme;