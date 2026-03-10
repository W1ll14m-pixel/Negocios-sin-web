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
import socket
import subprocess
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Módulos propios
from scraper_maps import buscar_negocios, crear_navegador_maps, cerrar_navegador, buscar_en_pagina
from generador_mensajes import procesar_prospectos
from exportador import exportar_csv, exportar_excel, mostrar_resumen
from whatsapp_sender import iniciar_envio_masivo
from gestor_contactados import (
    filtrar_nuevos_prospectos,
    guardar_contactado_individual,
    obtener_estadisticas,
    obtener_categorias_pendientes,
    marcar_categoria_buscada,
    calcular_faltantes_hoy,
    contar_enviados_hoy,
    obtener_ciudad_actual,
    guardar_ciudad_actual,
    obtener_ciudades_completadas,
    marcar_ciudad_completada,
    avanzar_a_siguiente_ciudad,
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
 ║   ✅ 100% AUTOMÁTICO — meta: 50 mensajes diarios            ║
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


def hay_internet() -> bool:
    """Verifica si hay conexión a internet intentando conectar a DNS de Google."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False


def esperar_conexion(intervalo: int = 30, max_espera: int = 3600):
    """
    Si no hay internet, espera hasta que vuelva la conexión.
    Reintenta cada `intervalo` segundos, hasta `max_espera` segundos total.
    Retorna True si la conexión volvió, False si se agotó el tiempo.
    """
    if hay_internet():
        return True

    console.print(Panel(
        "[bold red]🔌 SIN CONEXIÓN A INTERNET[/bold red]\n\n"
        f"Reintentando cada {intervalo} segundos...\n"
        f"Tiempo máximo de espera: {max_espera // 60} minutos",
        border_style="red",
    ))

    inicio = time.time()
    intentos = 0
    while time.time() - inicio < max_espera:
        intentos += 1
        time.sleep(intervalo)
        if hay_internet():
            console.print(f"[green]✅ Conexión restaurada (después de {intentos * intervalo}s)[/green]\n")
            return True
        minutos = int((time.time() - inicio) / 60)
        console.print(f"[yellow]⏳ Sin internet... ({minutos}min transcurridos)[/yellow]")

    console.print("[red]❌ No se pudo restaurar la conexión. Abortando.[/red]")
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
    archivos = [
        config.ARCHIVO_CONTACTADOS,
        config.ARCHIVO_HISTORICO,
        config.ARCHIVO_CATEGORIAS_BUSCADAS,
        config.ARCHIVO_CIUDAD_ACTUAL,
        config.ARCHIVO_CIUDADES_COMPLETADAS,
    ]
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
    Retorna la ciudad actual para buscar.
    Sistema SECUENCIAL: se agota una ciudad antes de pasar a la siguiente.
    Empieza por Cochabamba y avanza por departamentos.
    """
    completadas = obtener_ciudades_completadas()
    ciudad = obtener_ciudad_actual()

    # Si la ciudad actual ya está completada, avanzar
    if ciudad in completadas:
        ciudad = avanzar_a_siguiente_ciudad()
        if not ciudad:
            return None  # Todas completadas
    else:
        guardar_ciudad_actual(ciudad)

    return ciudad


def mostrar_config(ciudad: str, faltantes: int):
    """Muestra la configuración actual."""
    stats = obtener_estadisticas()
    categorias_pendientes = obtener_categorias_pendientes()
    total_cats = len(config.CATEGORIAS_NEGOCIOS)
    cats_pendientes = len(categorias_pendientes)
    completadas = obtener_ciudades_completadas()

    console.print(Panel(
        f"[cyan]📍 Ciudad actual:[/cyan] [bold]{ciudad}[/bold]\n"
        f"[cyan]🌐 Código de país:[/cyan] [bold]+{config.CODIGO_PAIS}[/bold]\n"
        f"[cyan]📊 Meta diaria:[/cyan] [bold]{config.MENSAJES_DIARIOS_META}[/bold]\n"
        f"[cyan]✅ Enviados hoy:[/cyan] [bold]{stats['enviados_hoy']}[/bold]\n"
        f"[cyan]📤 Faltan hoy:[/cyan] [bold]{faltantes}[/bold]\n"
        f"[cyan]📂 Categorías pendientes:[/cyan] [bold]{cats_pendientes}/{total_cats}[/bold]\n"
        f"[cyan]📋 Total contactados:[/cyan] [bold]{stats['total_contactados']}[/bold]\n"
        f"[cyan]🏙️  Ciudades completadas:[/cyan] [bold]{len(completadas)}/{len(config.CIUDADES_BOLIVIA)}[/bold]",
        title="⚙️ Configuración",
        border_style="cyan",
    ))


def busqueda_automatica(ciudad: str, limite: int) -> list[dict]:
    """
    Busca negocios SIN web hasta alcanzar el límite.
    Usa UN SOLO navegador para todas las búsquedas (más rápido y estable).
    Detecta errores de red y navegador cerrado, y se recupera automáticamente.
    Solo marca una categoría como buscada si la búsqueda fue exitosa.
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

    # ── Abrir navegador UNA VEZ para todas las búsquedas ──
    pw, browser, context, page = None, None, None, None
    navegador_abierto = False

    def abrir():
        nonlocal pw, browser, context, page, navegador_abierto
        if navegador_abierto:
            cerrar_navegador(pw, browser, context)
        pw, browser, context, page = crear_navegador_maps()
        navegador_abierto = True
        console.print("[green]✅ Navegador abierto.[/green]")

    def cerrar():
        nonlocal navegador_abierto
        if navegador_abierto:
            cerrar_navegador(pw, browser, context)
            navegador_abierto = False

    try:
        abrir()
    except Exception as e:
        console.print(f"[red]❌ Error al abrir navegador: {e}[/red]")
        return []

    try:
        categoria_idx = 0
        while len(todos_los_prospectos) < limite and categoria_idx < total_categorias:
            categoria = categorias[categoria_idx]
            termino = f"{categoria} en {ciudad}"

            console.print(Panel(
                f"[bold cyan]🔍 [{categoria_idx + 1}/{total_categorias}] {termino}[/bold cyan]\n"
                f"[dim]Encontrados: {len(todos_los_prospectos)}/{limite}[/dim]",
                border_style="cyan",
            ))

            # ── Reintentos por categoría (máx 3) ──
            MAX_REINTENTOS = 3
            categoria_ok = False

            for intento in range(MAX_REINTENTOS):
                # Asegurar que el navegador esté abierto
                if not navegador_abierto:
                    console.print("[yellow]🔄 Reabriendo navegador...[/yellow]")
                    try:
                        abrir()
                    except Exception as e:
                        console.print(f"[red]❌ No se pudo abrir navegador: {e}[/red]")
                        time.sleep(10)
                        continue

                faltantes = limite - len(todos_los_prospectos)
                cantidad_a_buscar = min(config.CANTIDAD_POR_CATEGORIA, faltantes + 5)

                resultado = buscar_en_pagina(page, termino, cantidad_a_buscar)
                negocios = resultado["negocios"]

                # ── Procesar negocios encontrados (incluso si fue error parcial) ──
                hay_nuevos = False
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
                        hay_nuevos = True
                        console.print(f"[green]✅ {len(prospectos_nuevos)} NUEVOS "
                                      f"— Total: {len(todos_los_prospectos)}/{limite}[/green]\n")

                if resultado["exito"]:
                    # ── Búsqueda completada exitosamente ──
                    if not hay_nuevos:
                        console.print("[yellow]⚠ Categoría agotada o sin resultados[/yellow]\n")
                        marcar_categoria_buscada(categoria)
                    categoria_ok = True
                    break  # Siguiente categoría

                else:
                    # ── Búsqueda falló ──
                    error_tipo = resultado["error_tipo"]

                    # Si ya obtuvimos resultados parciales, usarlos y seguir
                    if hay_nuevos:
                        console.print("[yellow]⚠ Búsqueda interrumpida pero se obtuvieron resultados.[/yellow]\n")
                        categoria_ok = True
                        if error_tipo == "navegador_cerrado":
                            navegador_abierto = False
                        break

                    # Sin resultados + error → reintentar según tipo de error
                    if error_tipo == "red":
                        console.print(f"[yellow]🔄 Error de red (intento {intento + 1}/{MAX_REINTENTOS})[/yellow]")
                        if not esperar_conexion():
                            break
                        # Tras reconexión, reabrir navegador por seguridad
                        cerrar()
                        time.sleep(3)
                        continue

                    elif error_tipo == "navegador_cerrado":
                        console.print(f"[yellow]🔄 Navegador cerrado (intento {intento + 1}/{MAX_REINTENTOS})[/yellow]")
                        navegador_abierto = False
                        time.sleep(5)
                        continue

                    elif error_tipo == "timeout":
                        console.print(f"[yellow]🔄 Timeout (intento {intento + 1}/{MAX_REINTENTOS})[/yellow]")
                        if not hay_internet():
                            if not esperar_conexion():
                                break
                            cerrar()
                            time.sleep(3)
                        else:
                            time.sleep(5)
                        continue

                    else:
                        # Error desconocido — no reintentar, no marcar como buscada
                        console.print("[yellow]⚠ Error desconocido. Saltando categoría.[/yellow]\n")
                        break

            if not categoria_ok:
                # No marcar como buscada — se reintentará en el futuro
                console.print(f"[yellow]⏭ '{categoria}' no procesada. Se reintentará luego.[/yellow]\n")

            if len(todos_los_prospectos) >= limite:
                console.print(f"\n[green]✅ Meta alcanzada: {limite} negocios[/green]")
                break

            categoria_idx += 1

            if categoria_idx < total_categorias:
                pausa = random.uniform(3, 6)
                time.sleep(pausa)

    except KeyboardInterrupt:
        console.print(f"\n[yellow]⚠ Búsqueda interrumpida[/yellow]")
    finally:
        cerrar()

    todos_los_prospectos = todos_los_prospectos[:limite]
    return todos_los_prospectos


def _log_paso(paso: int, total: int, descripcion: str):
    """Imprime un paso numerado con formato visible."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    console.print(f"\n[bold white on blue] PASO {paso}/{total} [/bold white on blue] "
                  f"[bold cyan]{descripcion}[/bold cyan] "
                  f"[dim]({timestamp})[/dim]\n")


def main():
    """Flujo principal 100% automático con loop hasta completar la meta."""
    console.print(BANNER)

    PASOS_TOTAL = 6

    # ── PASO 1: Verificar internet ──
    _log_paso(1, PASOS_TOTAL, "VERIFICANDO CONEXION A INTERNET")
    if not esperar_conexion():
        return
    console.print("[green]   OK — Internet disponible[/green]")

    # ── PASO 2: Sincronizar ──
    _log_paso(2, PASOS_TOTAL, "SINCRONIZANDO CON REPOSITORIO REMOTO")
    sincronizar_desde_remoto()

    # ── PASO 3: Calcular estado del dia ──
    _log_paso(3, PASOS_TOTAL, "CALCULANDO ESTADO DEL DIA")
    faltantes = calcular_faltantes_hoy()
    enviados_hoy = contar_enviados_hoy()
    console.print(f"   Enviados hoy: [bold]{enviados_hoy}[/bold]")
    console.print(f"   Meta diaria:  [bold]{config.MENSAJES_DIARIOS_META}[/bold]")
    console.print(f"   Faltan:       [bold]{faltantes}[/bold]")

    # ── PASO 4: Elegir ciudad ──
    _log_paso(4, PASOS_TOTAL, "ELIGIENDO CIUDAD")
    ciudad = elegir_ciudad()

    if not ciudad:
        console.print(Panel(
            "[bold green]🎉 TODAS LAS CIUDADES DE BOLIVIA COMPLETADAS[/bold green]\n\n"
            "Todos los negocios sin web han sido contactados.",
            border_style="green",
        ))
        return

    console.print(f"   Ciudad seleccionada: [bold]{ciudad}[/bold]")
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

    # ── PASO 5: LOOP PRINCIPAL — Buscar + Enviar ──
    _log_paso(5, PASOS_TOTAL, f"INICIANDO LOOP PRINCIPAL — META: {config.MENSAJES_DIARIOS_META} MENSAJES")
    MAX_RONDAS = 30  # Suficiente para completar 50 con fallos
    total_enviados_sesion = 0
    total_fallidos_sesion = 0
    ronda = 0

    while faltantes > 0 and ronda < MAX_RONDAS:
        ronda += 1

        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(Panel(
            f"[bold white on magenta] RONDA {ronda}/{MAX_RONDAS} [/bold white on magenta]  "
            f"[dim]({timestamp})[/dim]\n\n"
            f"  Enviados hoy:     [bold]{contar_enviados_hoy()}[/bold]\n"
            f"  Faltan:           [bold]{faltantes}[/bold]\n"
            f"  Ciudad:           [bold]{ciudad}[/bold]\n"
            f"  Sesión enviados:  [bold green]{total_enviados_sesion}[/bold green]\n"
            f"  Sesión fallidos:  [bold red]{total_fallidos_sesion}[/bold red]",
            title=f"Estado de la Ronda {ronda}",
            border_style="magenta",
        ))

        # 5a. Verificar internet
        console.print(f"  [cyan][5a] Verificando internet...[/cyan]")
        if not esperar_conexion():
            console.print("[red]   ❌ Sin internet. Guardando progreso...[/red]")
            subir_contactados_a_remoto()
            break
        console.print(f"  [green]   OK — Internet disponible[/green]")

        # 5b. Calcular cantidad a buscar
        buscar_cantidad = min(faltantes * 2, faltantes + 10)
        console.print(f"  [cyan][5b] Buscando {buscar_cantidad} negocios (extra para compensar fallos de ~40%)...[/cyan]")

        # 5c. BUSCAR negocios en Google Maps
        console.print(f"  [cyan][5c] ABRIENDO GOOGLE MAPS — Buscando negocios sin web...[/cyan]")
        nuevos = busqueda_automatica(ciudad, buscar_cantidad)

        if not nuevos:
            console.print(Panel(
                f"[bold yellow]🏙️  CIUDAD AGOTADA: {ciudad}[/bold yellow]\n\n"
                "Todas las categorías buscadas sin nuevos resultados.\n"
                "Avanzando a la siguiente ciudad...",
                border_style="yellow",
            ))
            marcar_ciudad_completada(ciudad)
            ciudad = avanzar_a_siguiente_ciudad()
            if not ciudad:
                console.print(Panel(
                    "[bold green]🎉 TODAS LAS CIUDADES DE BOLIVIA COMPLETADAS[/bold green]",
                    border_style="green",
                ))
                break
            continue

        console.print(f"  [green]   OK — {len(nuevos)} negocios encontrados[/green]")

        # 5d. Guardar prospectos en CSV/Excel
        console.print(f"  [cyan][5d] Guardando prospectos en CSV y Excel...[/cyan]")
        exportar_csv(nuevos)
        exportar_excel(nuevos)
        mostrar_resumen(nuevos)

        # 5e. ENVIAR por WhatsApp
        console.print(Panel(
            f"[bold cyan]📤 [5e] ENVIANDO {len(nuevos)} MENSAJES POR WHATSAPP[/bold cyan]\n\n"
            f"100% automático. Si no hay sesión activa,\n"
            f"escanea el QR cuando aparezca en el navegador.\n\n"
            f"[dim]Cada mensaje tiene pausa de 45-120s para evitar bloqueos.[/dim]",
            border_style="cyan",
        ))

        resultado_envio = iniciar_envio_masivo(nuevos)
        if resultado_envio is not None:
            nuevos = resultado_envio

        # 5f. Guardar contactados
        console.print(f"  [cyan][5f] Registrando contactados en historial...[/cyan]")
        guardados = 0
        for p in nuevos:
            try:
                guardar_contactado_individual(p)
                guardados += 1
            except Exception as e:
                console.print(f"  [red]   Error guardando {p.get('Nombre', '?')}: {e}[/red]")
        console.print(f"  [green]   OK — {guardados} contactos registrados[/green]")

        exportar_csv(nuevos)
        exportar_excel(nuevos)

        # 5g. Contar resultados
        enviados_ronda = len([p for p in nuevos if p.get("Estado") == "Enviado"])
        fallidos_ronda = len([p for p in nuevos if str(p.get("Estado", "")).startswith("Fallido")])
        total_enviados_sesion += enviados_ronda
        total_fallidos_sesion += fallidos_ronda

        console.print(Panel(
            f"[cyan]📊 RONDA {ronda} COMPLETADA[/cyan]\n\n"
            f"  ✅ Enviados esta ronda:   {enviados_ronda}\n"
            f"  ❌ Fallidos esta ronda:   {fallidos_ronda}\n"
            f"  ────────────────────────\n"
            f"  📈 Total sesión enviados: {total_enviados_sesion}\n"
            f"  📈 Total sesión fallidos: {total_fallidos_sesion}",
            border_style="cyan",
        ))

        # 5h. Subir al repositorio
        console.print(f"  [cyan][5h] Subiendo progreso al repositorio...[/cyan]")
        subir_contactados_a_remoto()

        # 5i. Recalcular faltantes
        faltantes = calcular_faltantes_hoy()
        console.print(f"  [cyan][5i] Faltantes recalculados: [bold]{faltantes}[/bold][/cyan]")

        if faltantes > 0:
            pausa = random.uniform(10, 20)
            console.print(f"\n  [yellow]⏳ Faltan {faltantes} mensajes. "
                          f"Pausa de {pausa:.0f}s antes de siguiente ronda...[/yellow]")
            time.sleep(pausa)
        else:
            console.print(f"\n  [bold green]🎉 META COMPLETADA — No faltan mas mensajes[/bold green]")

    # ── PASO 6: Resumen final ──
    _log_paso(6, PASOS_TOTAL, "RESUMEN FINAL")
    total_hoy = contar_enviados_hoy()

    if faltantes == 0:
        estado_msg = f"[bold green]🎉 META DIARIA COMPLETADA — {total_hoy}/{config.MENSAJES_DIARIOS_META}[/bold green]"
    else:
        estado_msg = (f"[bold yellow]⚠ Meta parcial: {total_hoy}/{config.MENSAJES_DIARIOS_META}[/bold yellow]\n"
                      f"Ejecuta de nuevo para continuar.")

    console.print(Panel(
        f"{estado_msg}\n\n"
        f"  ✅ Enviados esta sesión: {total_enviados_sesion}\n"
        f"  ❌ Fallidos esta sesión: {total_fallidos_sesion}\n"
        f"  🔄 Rondas ejecutadas:   {ronda}\n"
        f"  🏙️  Ciudad:              {ciudad}\n"
        f"  📁 Archivos: {config.ARCHIVO_CSV}, {config.ARCHIVO_HISTORICO}",
        title="SESION FINALIZADA",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
