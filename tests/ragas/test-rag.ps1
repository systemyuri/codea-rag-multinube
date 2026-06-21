# test-rag.ps1
# Script para probar preguntas del conjunto de validación con normalización de texto

param(
    [string]$ApiCode = "APgUNXw0hbrLWtTjXHnXUU6JwAXKjZbeMMa9enOmNYW9AzFup1vvTA==",
    [string]$QuestionsFile = "questions.json",
    [int]$SampleSize = 48,
    [string]$ApiUrl = "https://codea-orchestrator.azurewebsites.net/api/ask?code=$ApiCode"
)

# Verificar que el archivo existe
if (-not (Test-Path $QuestionsFile)) {
    Write-Error "No se encuentra el archivo: $QuestionsFile"
    exit 1
}

# Leer el archivo JSON
$questions = Get-Content -Path $QuestionsFile -Raw | ConvertFrom-Json

# Filtrar preguntas activas
$activeQuestions = $questions | Where-Object { $_.active -eq $true }

if ($activeQuestions.Count -eq 0) {
    Write-Warning "No hay preguntas activas en el archivo."
    exit 0
}

# Seleccionar muestra aleatoria
$sample = $activeQuestions | Get-Random -Count ([Math]::Min($SampleSize, $activeQuestions.Count))

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Prueba de $($sample.Count) preguntas aleatorias" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Función para normalizar texto (quitar tildes, diacríticos, convertir a minúsculas)
function Normalize-Text {
    param([string]$text)
    if ([string]::IsNullOrEmpty($text)) { return "" }
    
    # Convertir a minúsculas
    $normalized = $text.ToLowerInvariant()
    
    # Usar Normalize de .NET para separar caracteres base y diacríticos
    $normalized = $normalized.Normalize([System.Text.NormalizationForm]::FormD)
    
    # Eliminar caracteres diacríticos (tildes, etc.)
    $normalized = $normalized -replace '\p{M}', ''
    
    # Eliminar caracteres no alfanuméricos (excepto espacios, puntos, comas, paréntesis, guiones)
    $normalized = $normalized -replace '[^a-z0-9\s.,;:()\-]', ''
    
    return $normalized.Trim()
}

$results = @()

foreach ($q in $sample) {
    $questionText = $q.question
    $expected = $q.expectedAnswer
    $articles = $q.expectedArticles

    Write-Host "Pregunta: $questionText" -ForegroundColor Yellow

    # Enviar la pregunta al endpoint
    try {
        $body = @{ question = $questionText } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri $ApiUrl -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
        $answer = $response.answer

        # Normalizar textos para comparación
        $normalizedAnswer = Normalize-Text $answer
        $normalizedExpected = Normalize-Text $expected
        
        # Dividir la respuesta esperada en palabras clave (separadas por comas, puntos y comas, o "y")
        $keywords = $expected -split '[,;]\s*|\s+y\s+' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
        
        # Normalizar cada palabra clave
        $normalizedKeywords = $keywords | ForEach-Object { Normalize-Text $_ }
        
        $found = 0
        $foundDetails = @()
        foreach ($kw in $normalizedKeywords) {
            if ($normalizedAnswer -match [regex]::Escape($kw)) {
                $found++
                $foundDetails += $kw
            }
        }
        
        $score = if ($normalizedKeywords.Count -gt 0) { ($found / $normalizedKeywords.Count) * 100 } else { 0 }
        $passed = $score -ge 25  # Umbral flexible

        Write-Host "  Respuesta obtenida: $answer" -ForegroundColor Gray
        Write-Host "  Respuesta esperada: $expected" -ForegroundColor Green
        Write-Host "  Fuentes: $articles" -ForegroundColor Magenta
        Write-Host "  Coincidencia: $([math]::Round($score, 0))% ($found/$($normalizedKeywords.Count) palabras clave)" -ForegroundColor $(if ($passed) { "Green" } else { "Red" })
        if ($foundDetails.Count -gt 0) {
            Write-Host "  Palabras encontradas: $($foundDetails -join ', ')" -ForegroundColor Gray
        }
        Write-Host "  Estado: $(if ($passed) { 'APROBADO' } else { 'FALLIDO' })" -ForegroundColor $(if ($passed) { "Green" } else { "Red" })
        Write-Host ""

        $results += [PSCustomObject]@{
            Question = $questionText
            Expected = $expected
            Answer = $answer
            Score = $score
            Passed = $passed
        }
    }
    catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        $results += [PSCustomObject]@{
            Question = $questionText
            Expected = $expected
            Answer = "ERROR: $($_.Exception.Message)"
            Score = 0
            Passed = $false
        }
    }
}

# Resumen final
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RESUMEN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$passedCount = ($results | Where-Object { $_.Passed }).Count
$total = $results.Count
Write-Host "Aprobadas: $passedCount / $total ($([math]::Round(($passedCount/$total)*100, 0))%)" -ForegroundColor $(if ($passedCount -eq $total) { "Green" } else { "Yellow" })

if ($passedCount -lt $total) {
    Write-Host "Preguntas fallidas:" -ForegroundColor Red
    $results | Where-Object { -not $_.Passed } | ForEach-Object { Write-Host "  - $($_.Question)" -ForegroundColor Red }
}

Write-Host ""
Write-Host "Presiona cualquier tecla para salir..."
Read-Host