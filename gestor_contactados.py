# ============================================================
# gestor_contactados.py — Gestiona la lista de negocios
#                         ya contactados (anti-duplicados)
# ============================================================

import os
import pandas as pd
from datetime import datetime
from rich.console import Console

import config

console = Console()


def cargar_contactados() -> set:
    """
    Carga la lista de teléfonos ya contactados.
    
    Returns:
        Set con los teléfonos que YA fueron contactados.
    """
    if not os.path.exists(config.ARCHIVO_CONTACTADOS):
        return set()
    
    try:
        df = pd.read_csv(config.ARCHIVO_CONTACTADOS, encoding='utf-8-sig')
        telefónos = set(df['Telefono_Limpio'].astype(str).str.strip())
        console.print(f"[cyan]📋 {len(telefónos)} negocios ya contactados (historial cargado)[/cyan]")
        return telefónos
    except Exception as e:
        console.print(f"[yellow]⚠ Error cargando historial: {e}[/yellow]")
        return set()


def filtrar_nuevos_prospectos(prospectos: list[dict]) -> list[dict]:
    """
    Filtra los prospectos para excluir los que YA fueron contactados.
    
    Args:
        prospectos: Lista de prospectos encontrados.
    
    Returns:
        Lista de prospectos que NO han sido contactados aún.
    """
    contactados = cargar_contactados()
    
    nuevos = []
    duplicados = 0
    
    for p in prospectos:
        tel = str(p.get("Telefono_Limpio", "")).strip()
        if tel not in contactados:
            nuevos.append(p)
        else:
            duplicados += 1
    
    if duplicados > 0:
        console.print(f"[yellow]⚠ {duplicados} prospectos descartados (ya contactados)[/yellow]")
    
    return nuevos


def marcar_como_contactados(prospectos: list[dict]):
    """
    Guarda TODOS los prospectos procesados (enviados Y fallidos) en el historial
    para no volver a contactarlos. También agrega al archivo histórico para auditoría.

    Args:
        prospectos: Lista de prospectos procesados (cualquier estado excepto Pendiente).
    """
    # Guardar tanto enviados como fallidos para no reintentar
    procesados = [
        p for p in prospectos
        if p.get("Estado") and p.get("Estado") != "Pendiente"
    ]

    if not procesados:
        return

    enviados = [p for p in procesados if p.get("Estado") == "Enviado"]
    fallidos = [p for p in procesados if str(p.get("Estado", "")).startswith("Fallido")]

    # 1. Agregar a CONTACTADOS (para no volver a contactar)
    contactados_existentes = []
    if os.path.exists(config.ARCHIVO_CONTACTADOS):
        try:
            contactados_existentes = pd.read_csv(
                config.ARCHIVO_CONTACTADOS,
                encoding='utf-8-sig'
            ).to_dict('records')
        except Exception:
            pass

    # Agregar todos los procesados (enviados + fallidos)
    for p in procesados:
        contactados_existentes.append({
            "Nombre": p.get("Nombre", ""),
            "Telefono_Limpio": p.get("Telefono_Limpio", ""),
            "Fecha_Contacto": p.get("Fecha_Envio", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "Estado": p.get("Estado", ""),
        })

    # Guardar contactados
    df = pd.DataFrame(contactados_existentes)
    df.drop_duplicates(subset=['Telefono_Limpio'], keep='first', inplace=True)
    df.to_csv(config.ARCHIVO_CONTACTADOS, index=False, encoding='utf-8-sig')

    if enviados:
        console.print(f"[green]✅ {len(enviados)} contactos enviados guardados en historial[/green]")
    if fallidos:
        console.print(f"[yellow]⚠ {len(fallidos)} contactos fallidos registrados (no se reintentarán)[/yellow]")

    # 2. Agregar al archivo histórico (auditoría)
    historico_existente = []
    if os.path.exists(config.ARCHIVO_HISTORICO):
        try:
            historico_existente = pd.read_csv(
                config.ARCHIVO_HISTORICO,
                encoding='utf-8-sig'
            ).to_dict('records')
        except Exception:
            pass

    for p in procesados:
        historico_existente.append({
            "Fecha_Envio": p.get("Fecha_Envio", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "Nombre": p.get("Nombre", ""),
            "Telefono": p.get("Telefono_Limpio", ""),
            "Categoria": p.get("Categoria", ""),
            "Estado": p.get("Estado", ""),
        })

    df_historico = pd.DataFrame(historico_existente)
    df_historico.drop_duplicates(subset=['Telefono'], keep='first', inplace=True)
    df_historico.to_csv(config.ARCHIVO_HISTORICO, index=False, encoding='utf-8-sig')


def contar_enviados_hoy() -> int:
    """
    Cuenta cuántos mensajes se enviaron EXITOSAMENTE hoy.
    Lee el histórico y filtra por fecha de hoy y estado 'Enviado'.
    """
    if not os.path.exists(config.ARCHIVO_HISTORICO):
        return 0

    try:
        df = pd.read_csv(config.ARCHIVO_HISTORICO, encoding='utf-8-sig')
        hoy = datetime.now().strftime("%Y-%m-%d")
        # Filtrar por fecha de hoy Y estado enviado (no fallidos)
        df['Fecha_Envio'] = df['Fecha_Envio'].astype(str)
        enviados_hoy = df[
            (df['Fecha_Envio'].str.startswith(hoy)) &
            (df['Estado'].astype(str).str.startswith('Enviado'))
        ]
        return len(enviados_hoy)
    except Exception:
        return 0


def calcular_faltantes_hoy() -> int:
    """
    Calcula cuántos mensajes faltan para completar la meta diaria.
    """
    enviados = contar_enviados_hoy()
    faltantes = max(0, config.MENSAJES_DIARIOS_META - enviados)
    return faltantes


def obtener_estadisticas() -> dict:
    """
    Retorna estadísticas de contactos.
    """
    contactados = cargar_contactados()
    enviados_hoy = contar_enviados_hoy()
    faltantes_hoy = calcular_faltantes_hoy()

    stats = {
        "total_contactados": len(contactados),
        "enviados_hoy": enviados_hoy,
        "faltantes_hoy": faltantes_hoy,
        "meta_diaria": config.MENSAJES_DIARIOS_META,
        "archivo_contactados": config.ARCHIVO_CONTACTADOS,
        "archivo_historico": config.ARCHIVO_HISTORICO,
    }

    return stats


def cargar_categorias_buscadas() -> dict:
    """
    Carga las categorías que ya fueron completamente buscadas.

    Returns:
        Dict con {categoria: fecha_busqueda}
    """
    if not os.path.exists(config.ARCHIVO_CATEGORIAS_BUSCADAS):
        return {}

    try:
        df = pd.read_csv(config.ARCHIVO_CATEGORIAS_BUSCADAS, encoding='utf-8-sig')
        return dict(zip(df['Categoria'].astype(str), df['Fecha_Busqueda'].astype(str)))
    except Exception:
        return {}


def marcar_categoria_buscada(categoria: str):
    """
    Registra una categoría como completamente buscada (sin más resultados nuevos).
    """
    existentes = cargar_categorias_buscadas()
    existentes[categoria] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df = pd.DataFrame([
        {"Categoria": k, "Fecha_Busqueda": v}
        for k, v in existentes.items()
    ])
    df.to_csv(config.ARCHIVO_CATEGORIAS_BUSCADAS, index=False, encoding='utf-8-sig')


def obtener_categorias_pendientes() -> list[str]:
    """
    Retorna las categorías que aún no han sido completamente buscadas.
    """
    buscadas = cargar_categorias_buscadas()
    pendientes = [c for c in config.CATEGORIAS_NEGOCIOS if c not in buscadas]
    return pendientes
