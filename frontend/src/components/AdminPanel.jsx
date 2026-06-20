import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  IconButton,
  Button,
  CircularProgress,
  Typography,
  Snackbar,
  Alert,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Tooltip,
  InputAdornment,
} from '@mui/material';
import { Delete, Download, CloudUpload, Search, Refresh } from '@mui/icons-material';
import { format } from 'date-fns';
import { getDocuments, deleteDocument, getDownloadUrl, uploadFile, computeFileHash } from '../services/api';

export default function AdminPanel() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [deleteDialog, setDeleteDialog] = useState({ open: false, id: null, filename: '' });
  const [uploading, setUploading] = useState(false);

  const fetchDocuments = async (searchTerm = '') => {
    setLoading(true);
    try {
      const data = await getDocuments(searchTerm, 50, 0);
      setDocuments(data.documents || []);
    } catch (err) {
      setSnackbar({ open: true, message: 'Error al cargar documentos', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchDocuments(search);
  };

  const handleDelete = async () => {
    const { id, filename } = deleteDialog;
    try {
      await deleteDocument(id);
      setSnackbar({ open: true, message: `Documento "${filename}" eliminado`, severity: 'success' });
      fetchDocuments(search);
    } catch (err) {
      setSnackbar({ open: true, message: 'Error al eliminar', severity: 'error' });
    } finally {
      setDeleteDialog({ open: false, id: null, filename: '' });
    }
  };

  const handleDownload = async (id) => {
    try {
      const data = await getDownloadUrl(id);
      window.open(data.download_url, '_blank');
    } catch (err) {
      setSnackbar({ open: true, message: 'Error al descargar', severity: 'error' });
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setSnackbar({ open: true, message: 'Solo se permiten PDFs', severity: 'error' });
      return;
    }

    // === Extraer código y título del nombre ===
    let title = '';
    let normCode = '';
    let fileToUpload = file; // por defecto el original

    const separatorIndex = file.name.lastIndexOf('#');
    if (separatorIndex !== -1) {
      const codePart = file.name.substring(0, separatorIndex).trim();
      const titlePart = file.name.substring(separatorIndex + 1).replace(/\.pdf$/i, '').trim();
      const newName = `${codePart}.pdf`;
      // Crear un nuevo objeto File con el nombre limpio
      fileToUpload = new File([file], newName, { type: file.type });
      title = titlePart;
      normCode = codePart;
    } else {
      // Si no tiene separador, usar el nombre original como código y título
      normCode = file.name.replace(/\.pdf$/i, '');
      title = file.name.replace(/\.pdf$/i, '');
    }

    setUploading(true);
    try {
      const hash = await computeFileHash(file); // hash del contenido (no cambia por el nombre)
      // Llamar a uploadFile con los parámetros correctos
      await uploadFile(fileToUpload, hash, title, normCode);
      setSnackbar({ open: true, message: 'Archivo subido correctamente', severity: 'success' });
      fetchDocuments(search);
    } catch (err) {
      setSnackbar({ open: true, message: err.message || 'Error al subir', severity: 'error' });
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, flex: 1 }}>
          <TextField
            size="small"
            placeholder="Buscar por nombre..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ flex: 1 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton type="submit"><Search /></IconButton>
                </InputAdornment>
              ),
            }}
          />
          <IconButton onClick={() => fetchDocuments(search)}><Refresh /></IconButton>
        </form>
        <input
          accept=".pdf"
          style={{ display: 'none' }}
          id="upload-admin-file"
          type="file"
          onChange={handleFileUpload}
          disabled={uploading}
        />
        <label htmlFor="upload-admin-file">
          <Button
            variant="contained"
            component="span"
            startIcon={uploading ? <CircularProgress size={20} /> : <CloudUpload />}
            disabled={uploading}
          >
            {uploading ? 'Subiendo...' : 'Subir PDF'}
          </Button>
        </label>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nombre</TableCell>
              <TableCell>Fecha subida</TableCell>
              <TableCell>Tamaño (KB)</TableCell>
              <TableCell>Procesado</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={5} align="center"><CircularProgress /></TableCell></TableRow>
            ) : documents.length === 0 ? (
              <TableRow><TableCell colSpan={5} align="center">No hay documentos</TableCell></TableRow>
            ) : (
              documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.filename}</TableCell>
                  <TableCell>{doc.uploaded_at ? format(new Date(doc.uploaded_at), 'dd/MM/yyyy HH:mm') : '-'}</TableCell>
                  <TableCell>{doc.file_size_bytes ? (doc.file_size_bytes / 1024).toFixed(1) : '-'}</TableCell>
                  <TableCell>{doc.processed ? '✅' : '⏳'}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="Descargar">
                      <IconButton size="small" onClick={() => handleDownload(doc.id)}>
                        <Download />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Eliminar">
                      <IconButton size="small" onClick={() => setDeleteDialog({ open: true, id: doc.id, filename: doc.filename })}>
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={deleteDialog.open} onClose={() => setDeleteDialog({ open: false, id: null, filename: '' })}>
        <DialogTitle>Confirmar eliminación</DialogTitle>
        <DialogContent>
          <DialogContentText>
            ¿Estás seguro de eliminar el documento "{deleteDialog.filename}"? Esta acción no se puede deshacer.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, id: null, filename: '' })}>Cancelar</Button>
          <Button onClick={handleDelete} color="error">Eliminar</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}