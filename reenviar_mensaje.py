#!/usr/bin/env python3
# ============================================================
#  reenviar_mensaje.py — Reenvía el mensaje NUEVO a contactos
#                        que ya recibieron el mensaje anterior.
# ============================================================
#  - Lee contactados.csv, filtra los que tienen estado "Enviado"
#  - Excluye el número 59165317007
#  - Límite de 25 por día
#  - Guarda progreso en reenvio_progreso.csv para continuar
#    en días siguientes.
# ============================================================

import os
import sys
import time
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from whatsapp_sender import (
    enviar_mensaje_individual, verificar_vinculacion, detectar_bloqueo,
    _pausa_humana, _hay_internet, WHATSAPP_SESSION_DIR,
    PAUSA_ENTRE_MENSAJES_MIN, PAUSA_ENTRE_MENSAJES_MAX,
    MENSAJES_ANTES_PAUSA_LARGA, PAUSA_LARGA_MIN, PAUSA_LARGA_MAX,
    PAUSA_ENTRE_SESIONES,
)
from playwright.sync_api import sync_playwright
import config

console = Console()

# Archivo para rastrear progreso del reenvío
ARCHIVO_PROGRESO = os.path.join(os.path.dirname(__file__), "reenvio_progreso.csv")
NUMERO_EXCLUIDO = "59165317007"
MAX_POR_DIA = 25


def cargar_contactos_enviados() -> list[dict]:
    """Carga contactos que ya recibieron mensaje exitosamente."""
    if not os.path.exists(config.ARCHIVO_CONTACTADOS):
        return []
    df = pd.read_csv(config.ARCHIVO_CONTACTADOS, encoding='utf-8-sig')
    enviados = df[df['Estado'] == 'Enviado'].to_dict('records')
    return enviados


def cargar_ya_reenviados() -> set:
    """Carga teléfonos que ya recibieron el reenvío."""
    if not os.path.exists(ARCHIVO_PROGRESO):
        return set()
    df = pd.read_csv(ARCHIVO_PROGRESO, encoding='utf-8-sig')
    return set(df['Telefono_Limpio'].astype(str).str.strip())


def guardar_reenvio(nombre: str, telefono: str, estado: str):
    """Guarda un registro de reenvío."""
    fila = {
        "Nombre": nombre,
        "Telefono_Limpio": str(telefono).strip(),
        "Fecha_Reenvio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Estado": estado,
    }
    if os.path.exists(ARCHIVO_PROGRESO):
        df = pd.read_csv(ARCHIVO_PROGRESO, encoding='utf-8-sig')
        df = pd.concat([df, pd.DataFrame([fila])], ignore_index=True)
    else:
        df = pd.DataFrame([fila])
    df.to_csv(ARCHIVO_PROGRESO, index=False, encoding='utf-8-sig')


def contar_reenviados_hoy() -> int:
    """Cuenta cuántos reenvíos exitosos hubo hoy."""
    if not os.path.exists(ARCHIVO_PROGRESO):
        return 0
    df = pd.read_csv(ARCHIVO_PROGRESO, encoding='utf-8-sig')
    hoy = datetime.now().strftime("%Y-%m-%d")
    df_hoy = df[
        (df['Fecha_Reenvio'].str.startswith(hoy)) &
        (df['Estado'] == 'Reenviado')
    ]
    return len(df_hoy)


def main():
    console.print(Panel(
        "[bold cyan]📤 REENVÍO DEL NUEVO MENSAJE[/bold cyan]\n\n"
        "Envía el mensaje actualizado a todos los contactos\n"
        "que ya recibieron el mensaje anterior.\n\n"
        f"[bold]Límite diario: {MAX_POR_DIA} mensajes[/bold]\n"
        f"[bold]Excluido: {NUMERO_EXCLUIDO}[/bold]",
        border_style="cyan",
    ))

    # 1. Cargar contactos enviados previamente
    contactos = cargar_contactos_enviados()
    console.print(f"\n[green]📋 Contactos con envío exitoso previo: {len(contactos)}[/green]")

    # 2. Filtrar ya reenviados y número excluido
    ya_reenviados = cargar_ya_reenviados()
    pendientes = [
        c for c in contactos
        if str(c['Telefono_Limpio']).strip() not in ya_reenviados
        and str(c['Telefono_Limpio']).strip() != NUMERO_EXCLUIDO
    ]
    console.print(f"[yellow]⏳ Ya reenviados: {len(ya_reenviados)}[/yellow]")
    console.print(f"[cyan]📨 Pendientes de reenvío: {len(pendientes)}[/cyan]")

    if not pendientes:
        console.print("\n[green]✅ Todos los contactos ya recibieron el nuevo mensaje.[/green]")
        return

    # 3. Calcular cuántos faltan hoy
    enviados_hoy = contar_reenviados_hoy()
    restantes_hoy = max(0, MAX_POR_DIA - enviados_hoy)
    a_enviar = min(restantes_hoy, len(pendientes))

    console.print(f"\n[cyan]📊 Enviados hoy: {enviados_hoy}/{MAX_POR_DIA}[/cyan]")
    console.print(f"[bold]➡️  Se enviarán ahora: {a_enviar}[/bold]\n")

    if a_enviar == 0:
        console.print("[yellow]⚠ Ya se alcanzó el límite diario de 25 mensajes. Ejecuta mañana.[/yellow]")
        return

    # Mostrar lista
    for i, c in enumerate(pendientes[:a_enviar], 1):
        console.print(f"  {i}. {c.get('Nombre', '?')} — {c.get('Telefono_Limpio', '?')}")

    console.print()

    # 4. Generar nuevo mensaje para cada contacto
    # Usamos la plantilla actualizada de config.py
    # Necesitamos link_maps, que no está en contactados.csv
    # Se enviará el mensaje con nombre y sin link específico si no hay
    # Intentar buscar links del histórico o prospectos
    links = {}
    for csv_file in ["prospectos.csv", "historico_contactos.csv"]:
        path = os.path.join(os.path.dirname(__file__), csv_file)
        if os.path.exists(path):
            try:
                df_links = pd.read_csv(path, encoding='utf-8-sig')
                if 'Telefono_Limpio' in df_links.columns and 'Link_Maps' in df_links.columns:
                    for _, row in df_links.iterrows():
                        tel = str(row.get('Telefono_Limpio', '')).strip()
                        link = str(row.get('Link_Maps', '')).strip()
                        if tel and link and link != 'nan':
                            links[tel] = link
            except Exception:
                pass

    # 5. Abrir WhatsApp Web y enviar
    with sync_playwright() as pw:
        console.print("\n[cyan][WA-1] Abriendo navegador...[/cyan]")
        os.makedirs(WHATSAPP_SESSION_DIR, exist_ok=True)

        try:
            context = pw.chromium.launch_persistent_context(
                WHATSAPP_SESSION_DIR,
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                ]
            )
        except Exception as e:
            console.print(f"[red]❌ Error al abrir navegador: {e}[/red]")
            return

        page = context.pages[0] if context.pages else context.new_page()

        try:
            console.print("[cyan][WA-2] Navegando a web.whatsapp.com...[/cyan]")
            page.goto("https://web.whatsapp.com", timeout=config.TIMEOUT_PAGINA)

            console.print("[cyan][WA-3] Esperando vinculación...[/cyan]")
            console.print(Panel(
                "[bold green]📱 ESPERANDO VINCULACIÓN[/bold green]\n\n"
                "Si ya estás vinculado, cargará automáticamente.\n"
                "Si no, escanea el QR con tu teléfono.\n\n"
                "[dim]Tiempo máximo: 5 minutos[/dim]",
                border_style="green",
            ))

            vinculado = False
            for intento in range(60):
                time.sleep(5)
                vinculado = verificar_vinculacion(page)
                if vinculado:
                    break
                if intento > 0 and intento % 6 == 0:
                    console.print(f"[yellow]   ⏳ Esperando vinculación... ({intento * 5}s)[/yellow]")

            if not vinculado:
                console.print("[red]❌ No se vinculó WhatsApp Web.[/red]")
                context.close()
                return

            console.print("[bold green]   ✅ WhatsApp Web VINCULADO[/bold green]")
            time.sleep(3)

            # Enviar mensajes
            console.print(Panel(
                f"[bold green]📤 COMENZANDO REENVÍO DE {a_enviar} MENSAJES[/bold green]",
                border_style="green",
            ))

            enviados = 0
            fallidos = 0

            for prospecto in pendientes[:a_enviar]:
                nombre = prospecto.get("Nombre", "???")
                telefono = str(prospecto.get("Telefono_Limpio", "")).strip()

                # Construir mensaje con la plantilla actualizada
                link_maps = links.get(telefono, "https://maps.google.com")
                mensaje = config.PLANTILLA_MENSAJE.format(
                    nombre_negocio=nombre,
                    link_maps=link_maps,
                )

                timestamp = datetime.now().strftime("%H:%M:%S")
                console.print(f"\n[cyan]📤 [{enviados + 1}/{a_enviar}] "
                              f"({timestamp}) Reenviando a: [bold]{nombre}[/bold] ({telefono})[/cyan]")

                # Re-verificar vinculación cada 3 mensajes
                if enviados > 0 and enviados % 3 == 0:
                    console.print("   [dim]Revalidando vinculación...[/dim]")
                    page.goto("https://web.whatsapp.com", timeout=config.TIMEOUT_PAGINA)
                    time.sleep(5)
                    if not verificar_vinculacion(page):
                        console.print("[red]❌ WhatsApp se desvinculó. Deteniendo.[/red]")
                        break

                # Verificar bloqueo
                if detectar_bloqueo(page):
                    console.print("[red]🚫 Bloqueo detectado. Deteniendo.[/red]")
                    break

                resultado = enviar_mensaje_individual(page, telefono, mensaje)

                if resultado["exito"]:
                    enviados += 1
                    console.print(f"  [green]✅ REENVIADO — {resultado['motivo']}[/green]")
                    guardar_reenvio(nombre, telefono, "Reenviado")
                else:
                    fallidos += 1
                    console.print(f"  [red]❌ FALLIDO — {resultado['motivo']}[/red]")
                    guardar_reenvio(nombre, telefono, f"Fallido: {resultado['motivo']}")

                    if "Navegador cerrado" in resultado["motivo"]:
                        break
                    if "Sin internet" in resultado["motivo"]:
                        break

                # Pausas anti-bloqueo
                if enviados < a_enviar:
                    if enviados > 0 and enviados % MENSAJES_ANTES_PAUSA_LARGA == 0:
                        console.print(f"\n[yellow]⏸  Pausa larga...[/yellow]")
                        _pausa_humana(PAUSA_LARGA_MIN, PAUSA_LARGA_MAX,
                                      f"Pausa seguridad ({PAUSA_LARGA_MIN//60}-{PAUSA_LARGA_MAX//60} min)")
                    else:
                        _pausa_humana(PAUSA_ENTRE_MENSAJES_MIN, PAUSA_ENTRE_MENSAJES_MAX,
                                      "Pausa entre mensajes")

            # Resumen
            pendientes_restantes = len(pendientes) - enviados - fallidos
            console.print(Panel(
                f"[bold green]📊 RESUMEN DE REENVÍO[/bold green]\n\n"
                f"  ✅ Reenviados hoy: {enviados}\n"
                f"  ❌ Fallidos: {fallidos}\n"
                f"  ⏳ Pendientes total: {pendientes_restantes}\n\n"
                f"{'[yellow]Ejecuta de nuevo mañana para continuar.[/yellow]' if pendientes_restantes > 0 else '[green]¡Todos enviados![/green]'}",
                title="Reenvío Finalizado",
                border_style="green",
            ))

        except Exception as e:
            console.print(f"\n[bold red]❌ ERROR: {e}[/bold red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        finally:
            console.print("\n[cyan]Cerrando navegador...[/cyan]")
            try:
                context.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
