import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import GavelIcon from '@mui/icons-material/Gavel';

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