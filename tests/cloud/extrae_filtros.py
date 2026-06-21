import re

def extraer_filtros(pregunta):
    filtros = {}
    patrones = [
        (r"(Ley|DECRETO LEGISLATIVO|Decreto Supremo|RESOLUCION ADMINISTRATIVA|CONSTITUCION POLITICA)\s*([0-9-]+)", "norm_code"),
        (r'(".*?")', "title_exact"),
    ]
    for patron, clave in patrones:
        match = re.search(patron, pregunta, re.IGNORECASE)
        if match:
            if clave == "norm_code":
                tipo = match.group(1).strip()
                numero = match.group(2).strip()
                if tipo.upper() == "LEY":
                    filtros["norm_code"] = f"LEY {numero}"
                elif tipo.upper() == "DECRETO LEGISLATIVO":
                    filtros["norm_code"] = f"DECRETO LEGISLATIVO {numero}"
                elif tipo.upper() == "DECRETO SUPREMO":
                    filtros["norm_code"] = f"Decreto Supremo {numero}"
                elif "RESOLUCION" in tipo.upper():
                    filtros["norm_code"] = f"RESOLUCION ADMINISTRATIVA {numero}"
                elif "CONSTITUCION" in tipo.upper():
                    filtros["norm_code"] = "CONSTITUCION POLITICA 1993"
            else:
                filtros[clave] = match.group(1).strip('"')
    return filtros

pregunta = "¿Qué dice la Ley 27337 sobre pensiones de alimentos?"
print(extraer_filtros(pregunta))