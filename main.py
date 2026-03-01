#!/usr/bin/env python3
# ============================================================
#  main.py — SISTEMA AUTOMÁTICO DE PROSPECCIÓN SIN WEB
# ============================================================
#  100% AUTOMÁTICO — sin confirmaciones interactivas.
#  Busca negocios sin web en toda Bolivia, genera mensajes
#  personalizados, y envía por WhatsApp Web.
#
#  Meta: que cada negocio en el mundo tenga su página web.
# ============================================================

import os
import sys
import time
import random
import subprocess
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Módulos propios
from scraper_maps import buscar_negocios
from generador_mensajes import procesar_prospectos
from exportador import exportar_csv, exportar_excel, mostrar_resumen
from whatsapp_sender import iniciar_envio_masivo
from gestor_contactados import (
    filtrar_nuevos_prospectos,
    marcar_como_contactados,
    obtener_estadisticas,
    obtener_categorias_pendientes,
    marcar_categoria_buscada,
    calcular_faltantes_hoy,
    contar_enviados_hoy,
)
import config

console = Console()

# ── Banner ──────────────────────────────────────────────────
BANNER = """
[bold cyan]
 ╔══════════════════════════════════════════════════════════════╗
 ║                                                              ║
 ║   🌍  SISTEMA AUTOMÁTICO DE PROSPECCIÓN SIN WEB  🌍         ║
 ║                                                              ║
 ║   ✅ Busca CUALQUIER negocio en Google Maps                  ║
 ║   ✅ Filtra los que NO tienen página web                     ║
 ║   ✅ Genera mensajes personalizados                          ║
 ║   ✅ Nunca contacta el mismo negocio dos veces              ║
 ║   ✅ 100% AUTOMÁTICO — meta: 20 mensajes diarios            ║
 ║   ✅ Multi-ciudad: toda Bolivia                              ║
 ║                                                              ║
 ╚══════════════════════════════════════════════════════════════╝
[/bold cyan]
"""


def _run_git(args: list[str], timeout: int = 30) -> bool:
    """Ejecuta un comando git en el directorio del proyecto."""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True
        console.print(f"[yellow]⚠ git {' '.join(args)}: {result.stderr.strip()}[/yellow]")
        return False
    except Exception as e:
        console.print(f"[yellow]⚠ No se pudo ejecutar git: {e}[/yellow]")
        return False


def sincronizar_desde_remoto():
    """Descarga los últimos cambios del repositorio remoto."""
    console.print("[cyan]🔄 Sincronizando desde el repositorio remoto...[/cyan]")
    _run_git(["stash", "--include-untracked"])
    ok = _run_git(["pull", "--rebase", "origin", "main"], timeout=60)
    _run_git(["stash", "pop"])
    if ok:
        console.print("[green]✅ Sincronizado.[/green]")
    else:
        console.print("[yellow]⚠ No se pudo sincronizar — se usará historial local.[/yellow]")


def subir_contactados_a_remoto():
    """Sube archivos de contactados al repositorio remoto."""
    archivos = [config.ARCHIVO_CONTACTADOS, config.ARCHIVO_HISTORICO, config.ARCHIVO_CATEGORIAS_BUSCADAS]
    existentes = [f for f in archivos if os.path.exists(f)]
    if not existentes:
        return

    console.print("\n[cyan]☁️  Subiendo al repositorio remoto...[/cyan]")
    _run_git(["add"] + existentes)
    fecha = time.strftime("%Y-%m-%d %H:%M")
    _run_git(["commit", "-m", f"chore: actualizar contactados [{fecha}]"])
    ok = _run_git(["push", "origin", "main"], timeout=60)

    if ok:
        console.print("[green]✅ Historial subido al repositorio.[/green]")
    else:
        console.print("[yellow]⚠ No se pudo subir (se intentará la próxima vez).[/yellow]")


def elegir_ciudad() -> str:
    """
    Elige automáticamente la siguiente ciudad para buscar.
    Rota entre las ciudades de Bolivia basándose en la fecha
    para distribuir equitativamente.
    """
    dia_del_ano = datetime.now().timetuple().tm_yday
    hora = datetime.now().hour
    idx = (dia_del_ano * 3 + hora // 8) % len(config.CIUDADES_BOLIVIA)
    return config.CIUDADES_BOLIVIA[idx]


def mostrar_config(ciudad: str, faltantes: int):
    """Muestra la configuración actual."""
    stats = obtener_estadisticas()
    categorias_pendientes = obtener_categorias_pendientes()
    total_cats = len(config.CATEGORIAS_NEGOCIOS)
    cats_pendientes = len(categorias_pendientes)

    console.print(Panel(
        f"[cyan]📍 Ciudad:[/cyan] [bold]{ciudad}[/bold]\n"
        f"[cyan]🌐 Código de país:[/cyan] [bold]+{config.CODIGO_PAIS}[/bold]\n"
        f"[cyan]📊 Meta diaria:[/cyan] [bold]{config.MENSAJES_DIARIOS_META}[/bold]\n"
        f"[cyan]✅ Enviados hoy:[/cyan] [bold]{stats['enviados_hoy']}[/bold]\n"
        f"[cyan]📤 Faltan hoy:[/cyan] [bold]{faltantes}[/bold]\n"
        f"[cyan]📂 Categorías pendientes:[/cyan] [bold]{cats_pendientes}/{total_cats}[/bold]\n"
        f"[cyan]📋 Total contactados:[/cyan] [bold]{stats['total_contactados']}[/bold]\n"
        f"[cyan]🏙️  Ciudades disponibles:[/cyan] [bold]{len(config.CIUDADES_BOLIVIA)}[/bold]",
        title="⚙️ Configuración",
        border_style="cyan",
    ))


def busqueda_automatica(ciudad: str, limite: int) -> list[dict]:
    """
    Busca negocios SIN web hasta alcanzar el límite.
    Multi-ciudad, aleatoriza categorías, salta agotadas.
    """
    todos_los_prospectos = []

    categorias = obtener_categorias_pendientes()
    if not categorias:
        console.print("[yellow]⚠ Todas las categorías buscadas. Reiniciando...[/yellow]")
        categorias = list(config.CATEGORIAS_NEGOCIOS)

    random.shuffle(categorias)
    total_categorias = len(categorias)

    console.print(f"\n[bold yellow]🚀 BÚSQUEDA AUTOMÁTICA: {limite} negocios en {ciudad}[/bold yellow]")
    console.print(f"[cyan]   {total_categorias} categorías disponibles[/cyan]\n")

    categoria_idx = 0
    while len(todos_los_prospectos) < limite and categoria_idx < total_categorias:
        categoria = categorias[categoria_idx]
        termino = f"{categoria} en {ciudad}"

        console.print(Panel(
            f"[bold cyan]🔍 [{categoria_idx + 1}/{total_categorias}] {termino}[/bold cyan]\n"
            f"[dim]Encontrados: {len(todos_los_prospectos)}/{limite}[/dim]",
            border_style="cyan",
        ))

        try:
            faltantes = limite - len(todos_los_prospectos)
            cantidad_a_buscar = min(config.CANTIDAD_POR_CATEGORIA, faltantes + 5)

            negocios = buscar_negocios(termino, cantidad_a_buscar)

            if negocios:
                prospectos = procesar_prospectos(negocios)
                prospectos_nuevos = filtrar_nuevos_prospectos(prospectos)

                if prospectos_nuevos:
                    telefonos_sesion = {p["Telefono_Limpio"] for p in todos_los_prospectos}
                    prospectos_nuevos = [
                        p for p in prospectos_nuevos
                        if p["Telefono_Limpio"] not in telefonos_sesion
                    ]

                if prospectos_nuevos:
                    todos_los_prospectos.extend(prospectos_nuevos)
                    console.print(f"[green]✅ {len(prospectos_nuevos)} NUEVOS "
                                  f"— Total: {len(todos_los_prospectos)}/{limite}[/green]\n")
                else:
                    console.print(f"[yellow]⚠ Categoría agotada[/yellow]\n")
                    marcar_categoria_buscada(categoria)
            else:
                console.print(f"[yellow]⚠ Sin resultados[/yellow]\n")
                marcar_categoria_buscada(categoria)

        except KeyboardInterrupt:
            console.print(f"\n[yellow]⚠ Búsqueda interrumpida[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]\n")

        if len(todos_los_prospectos) >= limite:
            console.print(f"\n[green]✅ Meta alcanzada: {limite} negocios[/green]")
            break

        categoria_idx += 1

        if categoria_idx < total_categorias:
            pausa = random.uniform(5, 10)
            time.sleep(pausa)

    todos_los_prospectos = todos_los_prospectos[:limite]
    return todos_los_prospectos


def main():
    """Flujo principal 100% automático."""
    console.print(BANNER)

    # ── Sincronizar ──
    sincronizar_desde_remoto()

    # ── Calcular cuántos faltan hoy ──
    faltantes = calcular_faltantes_hoy()
    enviados_hoy = contar_enviados_hoy()

    # ── Elegir ciudad automáticamente ──
    ciudad = elegir_ciudad()

    mostrar_config(ciudad, faltantes)

    if faltantes == 0:
        console.print(Panel(
            f"[bold green]🎉 META DIARIA COMPLETADA[/bold green]\n\n"
            f"Ya se enviaron [bold]{enviados_hoy}/{config.MENSAJES_DIARIOS_META}[/bold] "
            f"mensajes hoy.\n\n"
            f"Ejecuta mañana para continuar.",
            border_style="green",
        ))
        return

    console.print(Panel(
        f"[bold green]🔍 BÚSQUEDA AUTOMÁTICA[/bold green]\n\n"
        f"Enviados hoy: [bold]{enviados_hoy}[/bold]\n"
        f"Faltan: [bold]{faltantes}[/bold] para completar la meta de "
        f"[bold]{config.MENSAJES_DIARIOS_META}[/bold]\n"
        f"Ciudad: [bold]{ciudad}[/bold]\n\n"
        f"Buscando negocios SIN web automáticamente...",
        border_style="green",
    ))

    # ── PASO 1: Buscar ──
    nuevos = busqueda_automatica(ciudad, faltantes)

    if not nuevos:
        console.print(Panel(
            "[bold yellow]⚠️ NO SE ENCONTRARON NEGOCIOS NUEVOS[/bold yellow]\n\n"
            "Se intentará con otra ciudad la próxima ejecución.",
            border_style="yellow",
        ))
        return

    # ── Guardar prospectos ──
    exportar_csv(nuevos)
    exportar_excel(nuevos)

    console.print(Panel(
        f"[bold green]📊 {len(nuevos)} NEGOCIOS ENCONTRADOS[/bold green]\n"
        f"Ciudad: [bold]{ciudad}[/bold]",
        border_style="green",
    ))
    mostrar_resumen(nuevos)

    # ── PASO 2: Enviar por WhatsApp (automático) ──
    console.print(Panel(
        f"[bold cyan]📤 ENVIANDO {len(nuevos)} MENSAJES POR WHATSAPP[/bold cyan]\n\n"
        f"100% automático. Si no hay sesión activa,\n"
        f"escanea el QR cuando aparezca en el navegador.",
        border_style="cyan",
    ))

    nuevos = iniciar_envio_masivo(nuevos) or nuevos

    # ── PASO 3: Guardar contactados ──
    console.print("\n[cyan]📋 Registrando contactados...[/cyan]")
    marcar_como_contactados(nuevos)
    exportar_csv(nuevos)
    exportar_excel(nuevos)

    # ── PASO 4: Subir al repositorio ──
    subir_contactados_a_remoto()

    # ── Resumen final ──
    enviados = len([p for p in nuevos if p.get("Estado") == "Enviado"])
    fallidos = len([p for p in nuevos if str(p.get("Estado", "")).startswith("Fallido")])
    total_hoy = contar_enviados_hoy()

    console.print(Panel(
        f"[bold green]🎉 SESIÓN COMPLETADA[/bold green]\n\n"
        f"✅ Enviados esta sesión: {enviados}\n"
        f"❌ Fallidos: {fallidos}\n"
        f"📊 Total enviados hoy: {total_hoy}/{config.MENSAJES_DIARIOS_META}\n"
        f"🏙️  Ciudad: {ciudad}\n"
        f"📁 Archivos: {config.ARCHIVO_CSV}, {config.ARCHIVO_HISTORICO}",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
