# ============================================================
# whatsapp_sender.py — Módulo de envío via WhatsApp Web
# ============================================================
# Maneja la vinculación con WhatsApp Web, verifica conexión,
# envía mensajes con pausas inteligentes anti-bloqueo,
# y detecta cuando WhatsApp limita los envíos masivos.
# ============================================================

import time
import random
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright.sync_api import TimeoutError as PwTimeout
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

import config

console = Console()

# Directorio para guardar la sesión de WhatsApp Web
WHATSAPP_SESSION_DIR = os.path.join(os.path.dirname(__file__), "whatsapp_session")

# --- Configuración de pausas anti-bloqueo ---
PAUSA_ENTRE_MENSAJES_MIN = 45    # Segundos mínimo entre mensajes
PAUSA_ENTRE_MENSAJES_MAX = 120   # Segundos máximo entre mensajes
MENSAJES_ANTES_PAUSA_LARGA = 5   # Cada N mensajes, pausa larga
PAUSA_LARGA_MIN = 300            # 5 minutos mínimo de pausa larga
PAUSA_LARGA_MAX = 600            # 10 minutos máximo de pausa larga
MAX_MENSAJES_POR_SESION = 20     # Máximo mensajes por sesión antes de parar
PAUSA_ENTRE_SESIONES = 3600      # 1 hora entre sesiones

# Textos que indican bloqueo o limitación
TEXTOS_BLOQUEO = [
    "temporalmente",
    "temporarily",
    "too many",
    "demasiados",
    "bloqueado",
    "blocked",
    "limit",
    "límite",
    "restricted",
    "restringido",
    "try again later",
    "intenta más tarde",
    "no se pudo enviar",
    "couldn't send",
    "failed to send",
]


def _pausa_humana(minimo: float, maximo: float, motivo: str = ""):
    """Pausa con cuenta regresiva visible."""
    tiempo = random.uniform(minimo, maximo)
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[cyan]⏳ {motivo} Esperando {{task.fields[remaining]}}s...[/cyan]"),
        console=console,
    ) as progress:
        task = progress.add_task("pausa", total=int(tiempo), remaining=int(tiempo))
        for i in range(int(tiempo)):
            time.sleep(1)
            progress.update(task, advance=1, remaining=int(tiempo) - i - 1)


def verificar_vinculacion(page: Page) -> bool:
    """
    Verifica que WhatsApp Web esté correctamente vinculado.
    Busca elementos que indiquen una sesión activa.
    
    Returns:
        True si está vinculado, False si no.
    """
    try:
        # Esperar a que cargue la página
        time.sleep(5)
        
        # Indicadores de que WhatsApp Web está vinculado:
        # 1. El buscador de chats aparece
        # 2. La lista de chats es visible
        # 3. NO hay código QR visible
        
        # Verificar si hay QR (= NO vinculado)
        qr_visible = False
        try:
            qr = page.locator('canvas[aria-label="Scan this QR code to link a device!"]').or_(
                page.locator('div[data-ref]')
            ).or_(
                page.locator('canvas').first
            )
            # Si encontramos el canvas del QR y es visible
            if qr.count() > 0 and qr.first.is_visible():
                qr_visible = True
        except Exception:
            pass
        
        if qr_visible:
            return False
        
        # Verificar si hay elementos de sesión activa
        sesion_activa = False
        selectores_sesion = [
            'div[contenteditable="true"][data-tab="3"]',   # Barra de búsqueda
            '#side',                                         # Panel lateral de chats
            'div[aria-label="Lista de chats"]',
            'div[aria-label="Chat list"]',
            'header',                                        # Header de WhatsApp
            'span[data-icon="search"]',                     # Ícono de búsqueda
            'div[data-tab="1"]',                            # Panel de chats
        ]
        
        for sel in selectores_sesion:
            try:
                el = page.locator(sel)
                if el.count() > 0 and el.first.is_visible():
                    sesion_activa = True
                    break
            except Exception:
                continue
        
        return sesion_activa
        
    except Exception as e:
        console.print(f"[red]Error verificando vinculación: {e}[/red]")
        return False


def detectar_bloqueo(page: Page) -> bool:
    """
    Detecta si WhatsApp ha limitado o bloqueado el envío de mensajes.
    
    Returns:
        True si se detectó un bloqueo/limitación.
    """
    try:
        # Obtener todo el texto visible en la página
        body_text = page.locator('body').inner_text().lower()
        
        for texto in TEXTOS_BLOQUEO:
            if texto.lower() in body_text:
                console.print(f"\n[bold red]🚫 ALERTA: Se detectó posible bloqueo ({texto})[/bold red]")
                return True
        
        # También verificar si aparecen pop-ups de error
        try:
            popups = page.locator('[role="alert"]').or_(
                page.locator('.popup-container')
            ).or_(
                page.locator('[data-animate-modal-popup="true"]')
            )
            if popups.count() > 0:
                popup_text = popups.first.inner_text().lower()
                for texto in TEXTOS_BLOQUEO:
                    if texto.lower() in popup_text:
                        return True
        except Exception:
            pass
            
    except Exception:
        pass
    
    return False


def enviar_mensaje_individual(page: Page, telefono: str, mensaje: str) -> dict:
    """
    Envía un mensaje a un número específico via WhatsApp Web.
    
    Returns:
        Dict con resultado: {'exito': bool, 'motivo': str}
    """
    try:
        import urllib.parse
        
        # Usar la URL directa de WhatsApp Web para abrir chat
        msg_encoded = urllib.parse.quote(mensaje, safe='')
        url = f"https://web.whatsapp.com/send?phone={telefono}&text={msg_encoded}"
        
        page.goto(url, timeout=config.TIMEOUT_PAGINA, wait_until="domcontentloaded")
        time.sleep(8)  # Esperar a que cargue completamente
        
        # Verificar si aparece "Número de teléfono no válido" o similar
        try:
            invalido = page.locator('div:has-text("invalid")').or_(
                page.locator('div:has-text("inválido")')
            ).or_(
                page.locator('div:has-text("no está en WhatsApp")')
            ).or_(
                page.locator('div:has-text("not on WhatsApp")')
            ).or_(
                page.locator('div:has-text("Phone number shared via url is invalid")')
            )
            
            # Buscar el popup/modal de número inválido
            popup = page.locator('div[data-animate-modal-popup="true"]')
            if popup.count() > 0:
                popup_text = popup.inner_text().lower()
                if "invalid" in popup_text or "inválido" in popup_text or "no está" in popup_text:
                    # Cerrar popup si hay botón OK
                    try:
                        ok_btn = popup.locator('div[role="button"]')
                        if ok_btn.count() > 0:
                            ok_btn.first.click()
                    except Exception:
                        pass
                    return {"exito": False, "motivo": "Número no tiene WhatsApp"}
        except Exception:
            pass
        
        # Esperar a que aparezca el campo de texto del chat
        try:
            input_field = page.locator(
                'div[contenteditable="true"][data-tab="10"]'
            ).or_(
                page.locator('div[contenteditable="true"][data-tab="6"]')
            ).or_(
                page.locator('footer div[contenteditable="true"]')
            )
            
            input_field.first.wait_for(state="visible", timeout=20000)
            time.sleep(2)
            
        except PwTimeout:
            # Si no aparece el campo de texto, el número puede no tener WhatsApp
            return {"exito": False, "motivo": "No se pudo abrir el chat (posible número sin WhatsApp)"}
        
        # El mensaje ya debería estar escrito por la URL, solo enviar
        # Buscar y hacer clic en el botón de enviar
        try:
            send_btn = page.locator('button[aria-label="Enviar"]').or_(
                page.locator('button[aria-label="Send"]')
            ).or_(
                page.locator('span[data-icon="send"]')
            )
            
            if send_btn.count() > 0:
                send_btn.first.click()
                time.sleep(3)
                return {"exito": True, "motivo": "Enviado correctamente"}
            else:
                # Intentar enviar con Enter
                input_field.first.press("Enter")
                time.sleep(3)
                return {"exito": True, "motivo": "Enviado (Enter)"}
                
        except Exception as e:
            return {"exito": False, "motivo": f"Error al hacer clic en enviar: {e}"}
        
    except PwTimeout:
        return {"exito": False, "motivo": "Timeout al cargar WhatsApp Web"}
    except Exception as e:
        return {"exito": False, "motivo": f"Error inesperado: {e}"}


def iniciar_envio_masivo(prospectos: list[dict]) -> list[dict]:
    """
    Envío 100% automático sin confirmaciones.
    1. Abre WhatsApp Web con sesión persistente
    2. Espera vinculación automáticamente
    3. Envía todos los mensajes pendientes
    4. Preserva la sesión para la próxima vez
    """
    if not prospectos:
        console.print("[yellow]⚠ No hay prospectos para enviar.[/yellow]")
        return prospectos

    pendientes = [p for p in prospectos if p.get("Estado") == "Pendiente"]
    if not pendientes:
        console.print("[yellow]⚠ Todos los prospectos ya fueron procesados.[/yellow]")
        return prospectos

    max_esta_sesion = min(MAX_MENSAJES_POR_SESION, len(pendientes))

    console.print(Panel(
        f"[bold cyan]📤 ENVÍO AUTOMÁTICO DE MENSAJES[/bold cyan]\n\n"
        f"Prospectos pendientes: [bold]{len(pendientes)}[/bold]\n"
        f"Se enviarán: [bold]{max_esta_sesion}[/bold] en esta sesión\n"
        f"Pausa entre mensajes: {PAUSA_ENTRE_MENSAJES_MIN}-{PAUSA_ENTRE_MENSAJES_MAX}s\n"
        f"Pausa larga cada {MENSAJES_ANTES_PAUSA_LARGA} mensajes: "
        f"{PAUSA_LARGA_MIN//60}-{PAUSA_LARGA_MAX//60} min",
        title="WhatsApp Web — Envío Automático",
        border_style="cyan",
    ))

    with sync_playwright() as pw:
        console.print("\n[cyan]🌐 Abriendo WhatsApp Web...[/cyan]\n")

        os.makedirs(WHATSAPP_SESSION_DIR, exist_ok=True)

        context: BrowserContext = pw.chromium.launch_persistent_context(
            WHATSAPP_SESSION_DIR,
            headless=False,
            viewport={"width": 1366, "height": 768},
            user_agent=config.USER_AGENT,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )

        page = context.pages[0] if context.pages else context.new_page()

        try:
            # 1. Navegar a WhatsApp Web
            page.goto("https://web.whatsapp.com", timeout=config.TIMEOUT_PAGINA)

            # 2. Esperar vinculación automáticamente
            console.print(Panel(
                "[bold green]📱 ESPERANDO VINCULACIÓN[/bold green]\n\n"
                "Si ya estás vinculado, cargará automáticamente.\n"
                "Si no, escanea el QR con tu teléfono.",
                title="Vinculación",
                border_style="green",
            ))

            vinculado = False
            max_intentos = 60  # 5 minutos
            for intento in range(max_intentos):
                time.sleep(5)
                vinculado = verificar_vinculacion(page)
                if vinculado:
                    break
                if intento > 0 and intento % 6 == 0:
                    console.print("[yellow]⏳ Esperando vinculación...[/yellow]")

            if not vinculado:
                console.print("[red]❌ No se vinculó WhatsApp Web después de 5 minutos.[/red]")
                context.close()
                return prospectos

            console.print("\n[bold green]✅ WhatsApp Web vinculado.[/bold green]\n")
            time.sleep(3)

            # 3. Verificación final
            console.print("[cyan]🔒 Verificando conexión...[/cyan]")
            if not verificar_vinculacion(page):
                console.print("[red]❌ Verificación final falló.[/red]")
                context.close()
                return prospectos

            console.print("[green]✅ Conexión verificada. Iniciando envío...[/green]\n")

            # 4. Enviar mensajes
            enviados = 0
            fallidos = 0
            bloqueado = False

            for i, prospecto in enumerate(prospectos):
                if prospecto.get("Estado") != "Pendiente":
                    continue

                if enviados >= max_esta_sesion:
                    console.print(f"\n[yellow]⚠ Límite de sesión alcanzado: {max_esta_sesion}[/yellow]")
                    break

                # Verificar bloqueo
                if detectar_bloqueo(page):
                    bloqueado = True
                    console.print(Panel(
                        "[bold red]🚫 BLOQUEO DETECTADO[/bold red]\n\n"
                        f"Se pausa {PAUSA_ENTRE_SESIONES//60} minutos...\n"
                        f"Enviados hasta ahora: {enviados}",
                        border_style="red",
                    ))
                    _pausa_humana(PAUSA_ENTRE_SESIONES, PAUSA_ENTRE_SESIONES + 600, "Pausa por bloqueo")
                    page.goto("https://web.whatsapp.com", timeout=config.TIMEOUT_PAGINA)
                    time.sleep(10)
                    if detectar_bloqueo(page):
                        console.print("[red]❌ Bloqueo persiste. Deteniendo.[/red]")
                        break
                    bloqueado = False

                nombre = prospecto.get("Nombre", "???")
                telefono = prospecto.get("Telefono_Limpio", "")
                mensaje = prospecto.get("Mensaje", "")

                console.print(f"\n[cyan]📤 [{enviados + 1}/{max_esta_sesion}] "
                              f"Enviando a: [bold]{nombre}[/bold] ({telefono})[/cyan]")

                # Re-verificar vinculación cada 3 mensajes
                if enviados > 0 and enviados % 3 == 0:
                    page.goto("https://web.whatsapp.com", timeout=config.TIMEOUT_PAGINA)
                    time.sleep(5)
                    if not verificar_vinculacion(page):
                        console.print("[red]❌ WhatsApp se desvinculó. Deteniendo.[/red]")
                        break

                # Enviar
                resultado = enviar_mensaje_individual(page, telefono, mensaje)

                if resultado["exito"]:
                    prospecto["Estado"] = "Enviado"
                    prospecto["Fecha_Envio"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    enviados += 1
                    console.print(f"  [green]✅ {resultado['motivo']}[/green]")
                else:
                    prospecto["Estado"] = f"Fallido: {resultado['motivo']}"
                    prospecto["Fecha_Envio"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    fallidos += 1
                    console.print(f"  [red]❌ {resultado['motivo']}[/red]")

                # Pausas
                if enviados < max_esta_sesion:
                    if enviados > 0 and enviados % MENSAJES_ANTES_PAUSA_LARGA == 0:
                        console.print(f"\n[yellow]⏸  Pausa larga (cada {MENSAJES_ANTES_PAUSA_LARGA} mensajes)...[/yellow]")
                        _pausa_humana(PAUSA_LARGA_MIN, PAUSA_LARGA_MAX,
                                      f"Pausa seguridad ({PAUSA_LARGA_MIN//60}-{PAUSA_LARGA_MAX//60} min)")
                    else:
                        _pausa_humana(PAUSA_ENTRE_MENSAJES_MIN, PAUSA_ENTRE_MENSAJES_MAX,
                                      "Pausa entre mensajes")

            # 5. Sesión preservada
            console.print("\n[cyan]📱 Sesión de WhatsApp preservada.[/cyan]")

            # 6. Resumen
            console.print(Panel(
                f"[bold green]📊 RESUMEN DE ENVÍO[/bold green]\n\n"
                f"✅ Enviados: {enviados}\n"
                f"❌ Fallidos: {fallidos}\n"
                f"⏳ Pendientes: {len([p for p in prospectos if p.get('Estado') == 'Pendiente'])}\n"
                f"{'🚫 Bloqueo detectado' if bloqueado else '✅ Sin bloqueos'}",
                title="Sesión Finalizada",
                border_style="green" if not bloqueado else "yellow",
            ))

        except Exception as e:
            console.print(f"[red]❌ Error durante el envío: {e}[/red]")
        finally:
            console.print("\n[cyan]Cerrando navegador...[/cyan]")
            try:
                context.close()
            except Exception:
                pass

    return prospectos
