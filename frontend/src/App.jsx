import { Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import GavelIcon from '@mui/icons-material/Gavel';
import InfoCard from './components/InfoCard';
import ChatMui from './components/ChatMui';

function App() {
  return (
    <>
      <AppBar position="static" color="primary">
        <Toolbar>
          <GavelIcon sx={{ mr: 2 }} />
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            CODEA
          </Typography>
          <Typography variant="subtitle2">
            Consulta de Demanda de Alimentos
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 3, mb: 4 }}>
        
        <ChatMui />
      </Container>

      <Box component="footer" sx={{ textAlign: 'center', py: 2, bgcolor: '#f0f2f5', mt: 4 }}>
        <Typography variant="caption" color="textSecondary">
          ⚖️ Información meramente orientativa. No reemplaza el asesoramiento legal profesional.
        </Typography>
      </Box>
    </>
  );
}

export default App;