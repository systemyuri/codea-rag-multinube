## 🗄️ Base de datos (AlloyDB)

Antes de desplegar los servicios, ejecuta los scripts SQL en el siguiente orden para preparar la base de datos:

1. `sql/01-create-extension-vector.sql` – habilita pgvector.
2. `sql/02-create-chunks-table.sql` – crea la tabla principal.
3. `sql/03-create-documentos-metadata-table.sql` – crea la tabla de metadatos.
4. `sql/04-create-indexes.sql` – crea índices para rendimiento.

Puedes ejecutarlos conectándote a AlloyDB con `psql`:
```bash
psql "host=<IP> user=postgres dbname=postgres" -f sql/01-create-extension-vector.sql
# ... repetir para los demás archivos