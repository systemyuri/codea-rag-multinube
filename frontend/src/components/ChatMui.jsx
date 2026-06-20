import { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Avatar,
  Typography,
  CircularProgress,
  Drawer,
  useMediaQuery,
  IconButton,
  Button,
  Tooltip,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import CloseIcon from '@mui/icons-material/Close';
import PersonIcon from '@mui/icons-material/Person';
import GavelIcon from '@mui/icons-material/Gavel';
import MenuIcon from '@mui/icons-material/Menu';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendQuestion } from '../services/api';
import InfoCard from './InfoCard';
import AdminLogin from './AdminLogin';
import AdminPanel from './AdminPanel';

export default function ChatMui() {
  const [messages, setMessages] = useState([
    { text: "Hola, soy CODEA. Puedo orientarte sobre requisitos, documentos y pasos para la pensión de alimentos en Perú. Recuerda que no soy un abogado.", isUser: false }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  
  // Estado para el panel de administración
  const [adminOpen, setAdminOpen] = useState(false);
  const [adminLoggedIn, setAdminLoggedIn] = useState(false);

  const isMobile = useMediaQuery('(max-width:900px)');

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setMessages(prev => [...prev, { text: userMsg, isUser: true }]);
    setInput('');
    setLoading(true);
    try {
      const answer = await sendQuestion(userMsg);
      setMessages(prev => [...prev, { text: answer, isUser: false }]);
    } catch (error) {
      console.error('[Chat] Error:', error);
      setMessages(prev => [...prev, { text: "Lo siento, ocurrió un error. Por favor intenta más tarde.", isUser: false }]);
    } finally {
      setLoading(false);
    }
  };

  // Cerrar sesión del administrador
  const handleAdminLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_token_expiry');
    setAdminLoggedIn(false);
  };

  const handleQuestionClick = (question) => {
  setInput(question);
  // Opcional: auto-enviar (descomenta si quieres que se envíe al hacer clic)
  // setTimeout(() => handleSend(), 100);
};

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#f0f2f5' }}>
      {/* Barra superior */}
      <Paper elevation={1} sx={{ p: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {isMobile && (
            <IconButton onClick={() => setDrawerOpen(true)}>
              <MenuIcon />
            </IconButton>
          )}
        </Box>
        <Typography variant="h6" sx={{ flexGrow: 1, textAlign: 'center' }}>
          CODEA - Asistente Legal
        </Typography>
        <Box>
          <Tooltip title="Administrar documentos">
            <IconButton 
              color={adminLoggedIn ? "primary" : "default"} 
              onClick={() => setAdminOpen(true)}
            >
              <AdminPanelSettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Sidebar fijo en escritorio */}
        {!isMobile && (
          <Box sx={{ width: 280, p: 2, overflowY: 'auto', borderRight: '1px solid #ddd' }}>
            <InfoCard onQuestionClick={handleQuestionClick}/>
          </Box>
        )}

        {/* Drawer en móvil */}
        <Drawer anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
          <Box sx={{ width: 280, p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
              <IconButton onClick={() => setDrawerOpen(false)}>
                <CloseIcon />
              </IconButton>
            </Box>
            <InfoCard />
          </Box>
        </Drawer>

        {/* Modal de login de administrador */}
        <AdminLogin
          open={adminOpen}
          onClose={() => setAdminOpen(false)}
          onLoginSuccess={() => {
            setAdminLoggedIn(true);
            setAdminOpen(false);
          }}
        />

        {/* Panel de administración (Drawer lateral derecho) */}
        <Drawer 
          anchor="right" 
          open={adminLoggedIn} 
          onClose={handleAdminLogout}
          PaperProps={{ sx: { width: { xs: '100%', sm: '80%', md: '70%' } } }}
        >
          <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5">Administración de Documentos</Typography>
              <Button variant="outlined" color="error" onClick={handleAdminLogout}>
                Cerrar sesión
              </Button>
            </Box>
            <AdminPanel />
          </Box>
        </Drawer>

        {/* Área central del chat */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 2, overflow: 'hidden' }}>
          <Paper elevation={3} sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', mb: 2 }}>
            <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
              {messages.map((msg, idx) => (
                <Box key={idx} sx={{ display: 'flex', justifyContent: msg.isUser ? 'flex-end' : 'flex-start', mb: 2 }}>
                  <Avatar sx={{ bgcolor: msg.isUser ? 'primary.main' : 'secondary.main', mr: msg.isUser ? 0 : 1, ml: msg.isUser ? 1 : 0 }}>
                    {msg.isUser ? <PersonIcon /> : <GavelIcon />}
                  </Avatar>
                  <Paper variant="outlined" sx={{ p: 1.5, maxWidth: '70%', bgcolor: msg.isUser ? 'primary.light' : 'background.paper' }}>
                    {msg.isUser ? (
                      <Typography variant="body2">{msg.text}</Typography>
                    ) : (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => (
                            <Typography variant="body2" paragraph sx={{ mb: 0.5, fontSize: '0.95rem' }}>
                              {children}
                            </Typography>
                          ),
                          li: ({ children }) => (
                            <li style={{ marginBottom: '2px' }}>{children}</li>
                          ),
                          strong: ({ children }) => (
                            <strong style={{ fontWeight: 'bold', color: '#0a3b5c' }}>{children}</strong>
                          ),
                          a: ({ href, children }) => (
                            <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2' }}>
                              {children}
                            </a>
                          ),
                          h3: ({ children }) => (
                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mt: 1, mb: 0.5 }}>
                              {children}
                            </Typography>
                          ),
                          ul: ({ children }) => (
                            <ul style={{ paddingLeft: '1.5rem', marginTop: '2px', marginBottom: '4px' }}>
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol style={{ paddingLeft: '1.5rem', marginTop: '2px', marginBottom: '4px' }}>
                              {children}
                            </ol>
                          ),
                          blockquote: ({ children }) => (
                            <blockquote style={{ borderLeft: '4px solid #1976d2', paddingLeft: '12px', margin: '8px 0', color: '#555' }}>
                              {children}
                            </blockquote>
                          ),
                          code: ({ inline, children }) =>
                            inline ? (
                              <code style={{ backgroundColor: '#f0f0f0', padding: '2px 4px', borderRadius: '4px', fontSize: '0.9rem' }}>
                                {children}
                              </code>
                            ) : (
                              <pre style={{ backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px', overflow: 'auto' }}>
                                <code>{children}</code>
                              </pre>
                            ),
                        }}
                      >
                        {msg.text}
                      </ReactMarkdown>
                    )}
                  </Paper>
                </Box>
              ))}
              {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={20} />
                  <Typography variant="caption">CODEA está escribiendo...</Typography>
                </Box>
              )}
            </Box>
          </Paper>

          {/* Caja de entrada */}
          <Box sx={{ display: 'flex', gap: 1, flexShrink: 0 }}>
            <TextField
              fullWidth
              variant="outlined"
              size="small"
              placeholder="Escribe tu pregunta (ej: ¿Qué documentos necesito?)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={loading}
            />
            <Button
              variant="contained"
              color="primary"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              endIcon={<SendIcon />}
            >
              Consultar
            </Button>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}