import { Card, CardContent, Typography, List, ListItem, ListItemIcon, ListItemText, Button, Box } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';

export default function InfoCard({ onQuestionClick }) {
  const suggestedQuestions = [
    "¿Cuántas cuotas impagas se necesitan para ser inscrito en el REDAM?",
    "¿Qué órgano del Poder Judicial administra el Registro de Deudores Alimentarios Morosos?",
    "¿Qué contenido debe tener el 'Certificado de Registro Positivo'?",
    "¿Qué principio rige en caso de duda sobre la admisión de pruebas en procesos de alimentos?",
    "En ausencia de los padres, ¿quién presta alimentos en primer orden según el Código de los Niños?",
    "¿Qué tipo de proceso se aplica a los alimentos según el Código Procesal Civil?",
    "¿Qué instituciones debe consultar el juez de oficio para conocer la capacidad económica del demandado?",
    "¿El demandante de alimentos está exonerado del pago de tasas judiciales?",
    "Enumere el orden de prelación de los obligados a prestar alimentos según el Código Civil.",
    "¿Qué medida cautelar debe disponer el auto admisorio en demanda de alimentos de niño o adolescente?"
  ];

  return (
    <Card sx={{ backgroundColor: '#eef2ff', height: '100%' }}>
      <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          🤔 ¿Cómo usar CODEA?
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          CODEA responde preguntas sobre <strong>pensión de alimentos en Perú</strong>. Usa solo leyes oficiales. No reemplaza a un abogado.
        </Typography>

        <Typography variant="subtitle2" fontSize="0.75rem" sx={{ mt: 1, mb: 0.5 }}>
          ✅ Puedes preguntar:          
        </Typography>
        <Box sx={{ maxHeight: 300, overflowY: 'auto', mb: 1 }}>
          {suggestedQuestions.map((q, idx) => (
            <Button
              key={idx}
              variant="text"
              size="small"
              fullWidth
              onClick={() => onQuestionClick(q)}
              sx={{
                justifyContent: 'flex-start',
                textTransform: 'none',
                fontSize: '0.75rem',
                p: 0.5,
                color: 'primary.main',
                borderBottom: '1px solid #e0e0e0',
                borderRadius: 0,
              }}
            >
              <span style={{ marginRight: '8px', fontSize: '1rem' }}>❓</span>
              <span style={{ textAlign: 'left' }}>{q}</span>
            </Button>
          ))}
        </Box>

        
        <Typography variant="subtitle2" fontSize="0.75rem">❌ No puedo:</Typography>
        <List dense disablePadding>
          <ListItem disablePadding sx={{ mb: 0.2 }}>
            <ListItemIcon sx={{ minWidth: 28 }}><WarningIcon color="warning" fontSize="small"/></ListItemIcon>
            <ListItemText primary="Calcular montos exactos" primaryTypographyProps={{ variant: 'caption' }}/>
          </ListItem>
          <ListItem disablePadding>
            <ListItemIcon sx={{ minWidth: 28 }}><WarningIcon color="warning" fontSize="small"/></ListItemIcon>
            <ListItemText primary="Actuar como abogado" primaryTypographyProps={{ variant: 'caption' }}/>
          </ListItem>
        </List>
        <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1 }}>
          * Respuesta orientativa. Consulta a un abogado.
        </Typography>
      </CardContent>
    </Card>
  );
}