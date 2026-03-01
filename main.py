#!/usr/bin/env python3
# ============================================================
#  main.py — SISTEMA AUTOMÁTICO DE PROSPECCIÓN SIN WEB
# ============================================================
#  Busca automáticamente negocios en Google Maps por múltiples
#  categorías, filtra los que NO tienen web, genera mensajes
#  personalizados, y envía por WhatsApp Web.
#  
#  ✅ Anti-duplicados: Nunca contacta dos veces el mismo negocio
#  ✅ Límite seguro: Máximo 10 mensajes por día
#  ✅ Verificación WhatsApp: Antes de enviar
#  ✅ Cierre de sesión: Después de terminar
# ============================================================

import os
import sys
import time
import random
import subprocess
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

# Módulos propios
from scraper_maps import buscar_negocios
from generador_mensajes import procesar_prospectos
from exportador import exportar_csv, exportar_excel, mostrar_resumen
from whatsapp_sender import iniciar_envio_masivo
from gestor_contactados import (
    filtrar_nuevos_prospectos,
    marcar_como_contactados,
    obtener_estadisticas
)
import config

console = Console()

# ── Banner ──────────────────────────────────────────────────
BANNER = """
[bold cyan]
 ╔══════════════════════════════════════════════════════════════╗
 ║                                                              ║
 ║   🔍  SISTEMA AUTOMÁTICO DE PROSPECCIÓN SIN WEB  🔍         ║
 ║                                                              ║
 ║   ✅ Busca CUALQUIER negocio en Google Maps                  ║
 ║   ✅ Filtra los que NO tienen página web                     ║
 ║   ✅ Genera mensajes personalizados                          ║
 ║   ✅ Nunca contacta el mismo negocio dos veces              ║
 ║   ✅ Límite seguro: 10 mensajes diarios máximo              ║
 ║                                                              ║
 ╚══════════════════════════════════════════════════════════════╝
[/bold cyan]
"""


def _run_git(args: list[str]) -> bool:
    """Ejecuta un comando git en el directorio del proyecto."""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True
        console.print(f"[yellow]⚠ git {' '.join(args)}: {result.stderr.strip()}[/yellow]")
        return False
    except Exception as e:
        console.print(f"[yellow]⚠ No se pudo ejecutar git: {e}[/yellow]")
        return False


def sincronizar_desde_remoto():
    """Descarga los últimos cambios del repositorio remoto (contactados actualizados)."""
    console.print("[cyan]🔄 Sincronizando historial de contactados desde el repositorio remoto...[/cyan]")
    ok = _run_git(["pull", "--rebase", "origin", "main"])
    if ok:
        console.print("[green]✅ Historial actualizado.[/green]")
    else:
        console.print("[yellow]⚠ No se pudo sincronizar — se usará historial local.[/yellow]")


def subir_contactados_a_remoto():
    """Sube contactados.csv e historico_contactos.csv al repositorio remoto."""
    archivos = [config.ARCHIVO_CONTACTADOS, config.ARCHIVO_HISTORICO]
    existentes = [f for f in archivos if os.path.exists(f)]
    if not existentes:
        return

    console.print("\n[cyan]☁️  Subiendo historial de contactados al repositorio remoto...[/cyan]")

    _run_git(["add"] + existentes)
    fecha = time.strftime("%Y-%m-%d %H:%M")
    _run_git(["commit", "-m", f"chore: actualizar contactados [{fecha}]"])
    ok = _run_git(["push", "origin", "main"])

    if ok:
        console.print("[green]✅ Historial de contactados subido al repositorio.[/green]")
    else:
        console.print("[yellow]⚠ No se pudo subir al repositorio (lo intentarás la próxima vez).[/yellow]")


def mostrar_config():
    """Muestra la configuración actual antes de arrancar."""
    stats = obtener_estadisticas()
    
    console.print(Panel(
        f"[cyan]📍 Ciudad:[/cyan] [bold]{config.CIUDAD}[/bold]\n"
        f"[cyan]🌐 Código de país:[/cyan] [bold]+{config.CODIGO_PAIS}[/bold]\n"
        f"[cyan]📊 Mensajes diarios (máx):[/cyan] [bold]{config.MENSAJES_DIARIOS_MAX}[/bold]\n"
        f"[cyan]📂 Categorías a buscar:[/cyan] [bold]{len(config.CATEGORIAS_NEGOCIOS)}[/bold]\n"
        f"[cyan]📋 Negocios ya contactados:[/cyan] [bold]{stats['total_contactados']}[/bold]",
        title="⚙️ Configuración",
        border_style="cyan",
    ))


def busqueda_automatica_limitada() -> list[dict]:
    """
    Busca negocios SIN web hasta alcanzar MENSAJES_DIARIOS_MAX.
    Filtra automáticamente los ya contactados.
    """
    todos_los_prospectos = []
    total_categorias = len(config.CATEGORIAS_NEGOCIOS)
    limite = config.MENSAJES_DIARIOS_MAX

    console.print(f"\n[bold yellow]🚀 BÚSQUEDA AUTOMÁTICA HASTA {limite} NUEVOS NEGOCIOS[/bold yellow]")
    console.print(f"[cyan]   Buscando en {total_categorias} categorías...[/cyan]\n")

    categoria_idx = 0
    while len(todos_los_prospectos) < limite and categoria_idx < total_categorias:
        categoria = config.CATEGORIAS_NEGOCIOS[categoria_idx]
        termino = f"{categoria} en {config.CIUDAD}"

        console.print(Panel(
            f"[bold cyan]🔍 [{categoria_idx + 1}/{total_categorias}] {termino}[/bold cyan]\n"
            f"[dim]Encontrados: {len(todos_los_prospectos)}/{limite}[/dim]",
            border_style="cyan",
        ))

        try:
            # Buscar negocios de esta categoría
            # Ajustar cantidad para alcanzar el límite
            faltantes = limite - len(todos_los_prospectos)
            cantidad_a_buscar = min(config.CANTIDAD_POR_CATEGORIA, faltantes + 5)
            
            negocios = buscar_negocios(termino, cantidad_a_buscar)

            if negocios:
                # Generar mensajes
                prospectos = procesar_prospectos(negocios)
                
                # FILTRAR: excluir ya contactados
                prospectos_nuevos = filtrar_nuevos_prospectos(prospectos)
                
                if prospectos_nuevos:
                    todos_los_prospectos.extend(prospectos_nuevos)
                    console.print(f"[green]✅ {len(prospectos_nuevos)} NUEVOS "
                                  f"— Total: {len(todos_los_prospectos)}/{limite}[/green]\n")
                else:
                    console.print(f"[yellow]⚠ Todos ya fueron contactados en esta categoría[/yellow]\n")
            else:
                console.print(f"[yellow]⚠ No se encontraron negocios sin web[/yellow]\n")

        except KeyboardInterrupt:
            console.print(f"\n[yellow]⚠ Búsqueda interrumpida[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]\n")

        # Si llegamos al límite, parar
        if len(todos_los_prospectos) >= limite:
            console.print(f"\n[green]✅ Se alcanzó el límite de {limite} nuevos negocios[/green]")
            break

        categoria_idx += 1
        
        # Pausa entre categorías
        if categoria_idx < total_categorias:
            pausa = random.uniform(5, 10)
            time.sleep(pausa)

    # Limitar exactamente al máximo
    todos_los_prospectos = todos_los_prospectos[:limite]
    return todos_los_prospectos


def main():
    """Flujo principal 100% automático."""
    console.print(BANNER)

    # ── Sincronizar historial desde el repositorio remoto ──────────
    sincronizar_desde_remoto()

    mostrar_config()

    # ── PASO 1: Buscar nuevos prospectos (solo los no contactados) ──
    console.print(Panel(
        "[bold green]🔍 PASO 1: BÚSQUEDA AUTOMÁTICA DE NUEVOS NEGOCIOS[/bold green]\n\n"
        f"Se buscarán hasta [bold]{config.MENSAJES_DIARIOS_MAX}[/bold] negocios "
        f"SIN página web en [bold]{config.CIUDAD}[/bold]\n"
        f"Se excluirán automáticamente los ya contactados.\n\n"
        "Se abrirá un navegador automático. [bold]No lo cierres.[/bold]",
        border_style="green",
    ))

    nuevos = busqueda_automatica_limitada()

    if not nuevos:
        console.print(Panel(
            "[bold yellow]⚠️ NO HAY NUEVOS NEGOCIOS PARA CONTACTAR[/bold yellow]\n\n"
            "Posibles razones:\n"
            "• Todos los negocios de estas categorías ya fueron contactados\n"
            "• Cambiar la ciudad en config.py\n"
            "• Buscar más tarde",
            border_style="yellow",
        ))
        return

    # Guardar prospectos temporales
    temp_df = pd.DataFrame(nuevos)
    exportar_csv(temp_df.to_dict('records'))
    exportar_excel(temp_df.to_dict('records'))

    # ── PASO 2: Resumen ──
    console.print(Panel(
        f"[bold green]📊 NUEVOS NEGOCIOS ENCONTRADOS[/bold green]\n\n"
        f"Total: [bold]{len(nuevos)}[/bold] negocios sin web\n"
        f"Guardados en: [bold]{config.ARCHIVO_CSV}[/bold]",
        border_style="green",
    ))

    mostrar_resumen(nuevos)

    # ── PASO 3: Enviar por WhatsApp ──
    console.print(Panel(
        "[bold yellow]📤 PASO 2: ENVÍO POR WHATSAPP WEB[/bold yellow]\n\n"
        f"Se enviarán [bold]{len(nuevos)}[/bold] mensajes personalizados.\n"
        f"Cada mensaje incluirá:\n"
        f"  • Nombre del negocio\n"
        f"  • Enlace de Google Maps\n"
        f"  • Oferta de página web\n\n"
        "[bold]Necesitarás escanear el QR con tu teléfono.[/bold]",
        border_style="yellow",
    ))

    if Confirm.ask("\n¿Enviar ahora?", default=True):
        nuevos = iniciar_envio_masivo(nuevos)

        # ── PASO 4: Guardar contactados ──
        console.print("\n[cyan]📋 Registrando negocios contactados...[/cyan]")
        marcar_como_contactados(nuevos)

        # Guardar resultado final
        exportar_csv(nuevos)
        exportar_excel(nuevos)

        # ── PASO 5: Subir historial al repositorio remoto ──
        subir_contactados_a_remoto()

        # Mostrar resumen
        enviados = len([p for p in nuevos if p.get("Estado") == "Enviado"])
        fallidos = len([p for p in nuevos if str(p.get("Estado", "")).startswith("Fallido")])

        console.print(Panel(
            f"[bold green]🎉 ENVÍO COMPLETADO[/bold green]\n\n"
            f"✅ Enviados: {enviados}\n"
            f"❌ Fallidos: {fallidos}\n"
            f"📁 Archivo: {config.ARCHIVO_CSV}\n"
            f"📋 Historial: {config.ARCHIVO_HISTORICO}",
            border_style="green",
        ))
    else:
        console.print("[cyan]Los prospectos están guardados. Ejecuta de nuevo para enviar.[/cyan]")


if __name__ == "__main__":
    main()
