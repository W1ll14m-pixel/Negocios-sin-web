# ============================================================
# scraper_maps.py — Módulo de scraping de Google Maps
# ============================================================
# Usa Playwright para navegar Google Maps, buscar negocios,
# extraer su información y filtrar los que NO tienen sitio web.
#
# Características:
# - Reutilización de navegador entre búsquedas
# - Detección de errores de red y navegador cerrado
# - Espera inteligente a que carguen los resultados
# - Reintentos automáticos en caso de fallos
# ============================================================

import time
import random
import re
import socket
from typing import Optional
from playwright.sync_api import (
    sync_playwright, Page, Browser, BrowserContext, Playwright,
    TimeoutError as PwTimeout,
)
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

import config

console = Console()

# Errores de red reintentables
ERRORES_RED = [
    "ERR_NAME_NOT_RESOLVED",
    "ERR_INTERNET_DISCONNECTED",
    "ERR_NETWORK_CHANGED",
    "ERR_TIMED_OUT",
    "ERR_CONNECTION_RESET",
    "ERR_CONNECTION_REFUSED",
    "ERR_ABORTED",
]


# ── Utilidades de red ─────────────────────────────────────────

def _hay_internet() -> bool:
    """Verifica si hay conexión a internet."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False


def _esperar_internet(max_espera: int = 300) -> bool:
    """Espera hasta que vuelva la conexión (máx 5 min por defecto)."""
    if _hay_internet():
        return True
    console.print("[bold red]🔌 Sin internet. Esperando reconexión...[/bold red]")
    inicio = time.time()
    while time.time() - inicio < max_espera:
        time.sleep(10)
        if _hay_internet():
            console.print("[green]✅ Internet restaurado.[/green]")
            return True
        console.print(f"[yellow]⏳ Sin internet... {int(time.time() - inicio)}s[/yellow]")
    return False


def _es_error_red(error: str) -> bool:
    """Verifica si un error es de tipo red/conexión."""
    return any(err in error for err in ERRORES_RED)


def _es_navegador_cerrado(error: str) -> bool:
    """Verifica si el error indica que el navegador/página se cerró."""
    indicadores = [
        "browser has been closed",
        "context has been closed",
        "target closed",
        "target page",
        "protocol error",
        "connection closed",
    ]
    error_lower = error.lower()
    return any(ind in error_lower for ind in indicadores)


# ── Utilidades generales ──────────────────────────────────────

def _pausa(minimo: float = None, maximo: float = None):
    """Pausa aleatoria para simular comportamiento humano."""
    mn = minimo or config.PAUSA_MIN
    mx = maximo or config.PAUSA_MAX
    tiempo = random.uniform(mn, mx)
    time.sleep(tiempo)


def _limpiar_texto(texto: str) -> str:
    """Limpia espacios extra y caracteres no deseados."""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()


def _extraer_telefono_limpio(telefono: str) -> str:
    """
    Limpia un número telefónico: quita espacios, guiones, paréntesis.
    Devuelve solo dígitos con código de país.
    """
    if not telefono:
        return ""
    limpio = re.sub(r'[^\d+]', '', telefono)
    if limpio.startswith('+'):
        limpio = limpio[1:]
    if not limpio.startswith(config.CODIGO_PAIS):
        if limpio.startswith('0'):
            limpio = limpio[1:]
        limpio = config.CODIGO_PAIS + limpio
    return limpio


# ── Funciones de scraping ─────────────────────────────────────

def _scroll_resultados(page: Page):
    """Hace scroll en el panel de resultados de Google Maps."""
    try:
        panel = page.locator('div[role="feed"]')
        if panel.count() > 0:
            panel.evaluate('el => el.scrollTop = el.scrollHeight')
        else:
            page.mouse.wheel(0, 800)
    except Exception:
        page.mouse.wheel(0, 800)


def _esperar_carga_resultados(page: Page, timeout: int = 20) -> bool:
    """
    Espera a que se carguen los resultados de Google Maps.
    Returns True si se encontraron resultados, False si no.
    """
    try:
        # Esperar a que aparezca el contenedor de resultados (feed)
        page.wait_for_selector('div[role="feed"]', timeout=timeout * 1000)
        time.sleep(3)  # Dar tiempo al JS para renderizar los items

        # Verificar que haya links de negocios dentro del feed
        intentos = 0
        while intentos < 8:
            links = page.locator('a[href*="/maps/place/"]')
            if links.count() > 0:
                return True
            intentos += 1
            time.sleep(1)

        return False
    except PwTimeout:
        return False
    except Exception:
        return False


def _obtener_urls_negocios(page: Page, cantidad_deseada: int) -> list[str]:
    """
    Hace scroll en los resultados de Maps hasta obtener
    la cantidad deseada de URLs de negocios.
    """
    urls_encontradas = set()
    scrolls_sin_nuevos = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Buscando negocios..."),
        BarColumn(),
        TextColumn("[green]{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scrolling", total=cantidad_deseada)

        while len(urls_encontradas) < cantidad_deseada:
            links = page.locator('a[href*="/maps/place/"]').all()
            cantidad_anterior = len(urls_encontradas)

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/maps/place/' in href and href not in urls_encontradas:
                        urls_encontradas.add(href)
                        progress.update(task, completed=min(len(urls_encontradas), cantidad_deseada))
                        if len(urls_encontradas) >= cantidad_deseada:
                            break
                except Exception:
                    continue

            if len(urls_encontradas) == cantidad_anterior:
                scrolls_sin_nuevos += 1
                if scrolls_sin_nuevos >= config.MAX_SCROLLS_SIN_RESULTADOS:
                    console.print(
                        f"\n[yellow]⚠ No se encontraron más resultados después de "
                        f"{scrolls_sin_nuevos} intentos. "
                        f"Se obtuvieron {len(urls_encontradas)} de {cantidad_deseada}.[/yellow]"
                    )
                    break
            else:
                scrolls_sin_nuevos = 0

            _scroll_resultados(page)
            _pausa(config.PAUSA_SCROLL_MIN, config.PAUSA_SCROLL_MAX)

            # Verificar si llegamos al final de resultados
            try:
                fin = page.locator('text="No hay más resultados"').or_(
                    page.locator('text="Has llegado al final de la lista"')
                ).or_(
                    page.locator('span.HlvSq')
                )
                if fin.count() > 0:
                    console.print("\n[yellow]⚠ Se alcanzó el final de los resultados.[/yellow]")
                    break
            except Exception:
                pass

    return list(urls_encontradas)[:cantidad_deseada]


def _extraer_info_negocio(page: Page, url: str) -> Optional[dict]:
    """
    Navega a la página de un negocio en Maps y extrae su info.
    Si el navegador se cerró, lanza la excepción para que el caller se recupere.
    """
    try:
        page.goto(url, timeout=config.TIMEOUT_PAGINA, wait_until="domcontentloaded")
        _pausa(2, 4)

        # --- NOMBRE del negocio ---
        nombre = ""
        try:
            nombre_el = page.locator('h1.DUwDvf').first
            if nombre_el.count() > 0:
                nombre = _limpiar_texto(nombre_el.inner_text())
            else:
                nombre_el = page.locator('h1').first
                nombre = _limpiar_texto(nombre_el.inner_text())
        except Exception:
            nombre = "Negocio sin nombre"

        if not nombre:
            return None

        # --- Verificar si TIENE SITIO WEB (si tiene, lo descartamos) ---
        tiene_web = False
        try:
            web_selectors = [
                'a[data-item-id="authority"]',
                'a[aria-label*="Sitio web"]',
                'a[aria-label*="sitio web"]',
                'a[aria-label*="Website"]',
                'a[aria-label*="website"]',
                'button[data-item-id="authority"]',
                'a[data-tooltip="Abrir sitio web"]',
                'a[data-tooltip="Open website"]',
            ]
            for sel in web_selectors:
                if page.locator(sel).count() > 0:
                    tiene_web = True
                    break
        except Exception:
            pass

        if tiene_web:
            console.print(f"  [dim]✗ {nombre} — YA tiene sitio web. Ignorado.[/dim]")
            return None

        # --- TELÉFONO ---
        telefono = ""
        try:
            tel_selectors = [
                'button[data-item-id^="phone:"] .Io6YTe',
                'button[data-item-id^="phone:"]',
                'a[data-item-id^="phone:"]',
                'button[aria-label*="Teléfono"]',
                'button[aria-label*="Phone"]',
                '[data-tooltip="Copiar número de teléfono"]',
                '[data-tooltip="Copy phone number"]',
            ]
            for sel in tel_selectors:
                el = page.locator(sel).first
                if el.count() > 0:
                    aria = el.get_attribute('aria-label')
                    if aria:
                        numeros = re.findall(r'[\d\s\-\+\(\)]+', aria)
                        if numeros:
                            telefono = max(numeros, key=len).strip()
                            break
                    txt = el.inner_text()
                    if txt and re.search(r'\d', txt):
                        telefono = _limpiar_texto(txt)
                        break
                    data_id = el.get_attribute('data-item-id')
                    if data_id and data_id.startswith('phone:'):
                        telefono = data_id.replace('phone:tel:', '').replace('phone:', '')
                        break
        except Exception:
            pass

        if not telefono:
            console.print(f"  [dim]✗ {nombre} — Sin teléfono. Ignorado.[/dim]")
            return None

        telefono_limpio = _extraer_telefono_limpio(telefono)

        if not telefono_limpio or len(telefono_limpio) < 8:
            console.print(f"  [dim]✗ {nombre} — Teléfono inválido: {telefono}. Ignorado.[/dim]")
            return None

        # --- CATEGORÍA del negocio ---
        categoria = ""
        try:
            cat_el = page.locator('button.DkEaL').first
            if cat_el.count() > 0:
                categoria = _limpiar_texto(cat_el.inner_text())
        except Exception:
            pass

        # --- DIRECCIÓN ---
        direccion = ""
        try:
            dir_selectors = [
                'button[data-item-id="address"] .Io6YTe',
                'button[data-item-id="address"]',
                '[data-item-id="address"]',
            ]
            for sel in dir_selectors:
                el = page.locator(sel).first
                if el.count() > 0:
                    aria = el.get_attribute('aria-label')
                    if aria:
                        direccion = _limpiar_texto(aria.replace('Dirección:', '').replace('Address:', ''))
                        break
                    direccion = _limpiar_texto(el.inner_text())
                    break
        except Exception:
            pass

        console.print(f"  [green]✓ {nombre}[/green] — Tel: {telefono_limpio}")

        return {
            "nombre": nombre,
            "telefono_original": telefono,
            "telefono_limpio": telefono_limpio,
            "categoria": categoria,
            "direccion": direccion,
            "link_maps": url,
            "tiene_web": False,
        }

    except PwTimeout:
        console.print(f"  [red]✗ Timeout al cargar: {url[:60]}...[/red]")
        return None
    except Exception as e:
        error_str = str(e)
        # Si el navegador se cerró, propagar para que el caller se recupere
        if _es_navegador_cerrado(error_str):
            raise
        console.print(f"  [red]✗ Error al extraer datos: {e}[/red]")
        return None


# ── API pública (reutilización de navegador) ──────────────────

def crear_navegador_maps():
    """
    Crea un navegador para scraping de Maps.
    Returns: (playwright, browser, context, page)
    El caller debe cerrar con cerrar_navegador() cuando termine.
    """
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
        ]
    )
    context = browser.new_context(
        viewport={"width": 1366, "height": 768},
        user_agent=config.USER_AGENT,
        locale='es-ES',
        timezone_id='America/La_Paz',
    )
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    page = context.new_page()
    return pw, browser, context, page


def cerrar_navegador(pw, browser, context):
    """Cierra todos los recursos del navegador de forma segura."""
    for recurso, metodo in [(context, "close"), (browser, "close"), (pw, "stop")]:
        try:
            getattr(recurso, metodo)()
        except Exception:
            pass


def buscar_en_pagina(page: Page, termino: str, cantidad: int) -> dict:
    """
    Busca negocios sin web usando una página de navegador existente.

    Returns:
        {
            "negocios": list[dict],   # Negocios encontrados (puede ser parcial si hubo error)
            "exito": bool,            # True si la búsqueda completó sin errores
            "error_tipo": str|None,   # None, "red", "navegador_cerrado", "timeout"
        }
    """
    resultados = []

    console.print(f"\n[bold cyan]🔍 Buscando: '{termino}' — Objetivo: {cantidad} negocios sin web[/bold cyan]\n")

    try:
        # 1. Verificar internet antes de buscar
        if not _hay_internet():
            if not _esperar_internet():
                return {"negocios": [], "exito": False, "error_tipo": "red"}

        # 2. Navegar a Google Maps con la búsqueda
        url_busqueda = f"https://www.google.com/maps/search/{termino.replace(' ', '+')}"
        console.print("[cyan]📡 Navegando a Google Maps...[/cyan]")
        page.goto(url_busqueda, timeout=config.TIMEOUT_PAGINA, wait_until="domcontentloaded")

        # 3. Aceptar cookies si aparece el diálogo
        try:
            accept_btn = page.locator('button:has-text("Aceptar todo")').or_(
                page.locator('button:has-text("Accept all")')
            )
            if accept_btn.count() > 0:
                accept_btn.first.click()
                _pausa(1, 2)
        except Exception:
            pass

        # 4. Esperar a que carguen los resultados (CLAVE: no hacer scroll antes)
        console.print("[cyan]⏳ Esperando que carguen los resultados...[/cyan]")
        resultados_cargados = _esperar_carga_resultados(page)

        if not resultados_cargados:
            # Verificar si Maps dice "sin resultados" (búsqueda válida pero vacía)
            sin_resultados = False
            try:
                body_text = page.locator('body').inner_text(timeout=5000).lower()
                textos_sin_resultados = [
                    "no results", "sin resultados", "no se encontraron",
                    "nada que coincida", "tu búsqueda no tuvo resultados",
                ]
                sin_resultados = any(t in body_text for t in textos_sin_resultados)
            except Exception:
                pass

            if sin_resultados:
                console.print("[yellow]⚠ Google Maps no encontró resultados para esta búsqueda.[/yellow]")
                return {"negocios": [], "exito": True, "error_tipo": None}

            # No hay feed ni texto de "sin resultados" — podría ser carga lenta
            console.print("[yellow]⚠ Carga lenta. Esperando más tiempo...[/yellow]")
            _pausa(5, 8)

            # Segundo intento de espera
            if not _esperar_carga_resultados(page, timeout=15):
                # Verificar si la página está en blanco o rota
                try:
                    url_actual = page.url
                    if "maps" not in url_actual.lower():
                        console.print("[red]❌ La página no cargó correctamente.[/red]")
                        return {"negocios": [], "exito": False, "error_tipo": "timeout"}
                except Exception:
                    pass
                console.print("[yellow]⚠ No se pudieron cargar resultados después de esperar.[/yellow]")
                return {"negocios": [], "exito": True, "error_tipo": None}

        # 5. Scroll para obtener URLs de negocios
        console.print("[cyan]📜 Haciendo scroll para cargar resultados...[/cyan]")
        urls = _obtener_urls_negocios(page, cantidad * 3)
        console.print(f"\n[cyan]📋 Se encontraron {len(urls)} negocios totales para analizar.[/cyan]\n")

        if not urls:
            console.print("[yellow]⚠ No se encontraron negocios.[/yellow]")
            return {"negocios": [], "exito": True, "error_tipo": None}

        # 6. Visitar cada negocio y extraer datos
        console.print("[bold cyan]🔎 Analizando cada negocio...[/bold cyan]\n")
        for i, url in enumerate(urls, 1):
            if len(resultados) >= cantidad:
                console.print(f"\n[green]✅ Se alcanzó la cantidad deseada: {cantidad} negocios.[/green]")
                break

            console.print(f"[cyan]  [{i}/{len(urls)}] Analizando...[/cyan]")
            info = _extraer_info_negocio(page, url)

            if info:
                resultados.append(info)

            _pausa()

        console.print(f"\n[bold green]📊 Resultado: {len(resultados)} negocios SIN web encontrados.[/bold green]\n")
        return {"negocios": resultados, "exito": True, "error_tipo": None}

    except PwTimeout:
        console.print("[red]❌ Timeout: Google Maps tardó demasiado en cargar.[/red]")
        return {"negocios": resultados, "exito": False, "error_tipo": "timeout"}
    except Exception as e:
        error_str = str(e)
        if _es_navegador_cerrado(error_str):
            console.print("[red]❌ El navegador se cerró inesperadamente.[/red]")
            return {"negocios": resultados, "exito": False, "error_tipo": "navegador_cerrado"}
        if _es_error_red(error_str):
            console.print(f"[red]❌ Error de red: {e}[/red]")
            return {"negocios": resultados, "exito": False, "error_tipo": "red"}
        console.print(f"[red]❌ Error durante la búsqueda: {e}[/red]")
        return {"negocios": resultados, "exito": False, "error_tipo": "desconocido"}


def buscar_negocios(termino: str, cantidad: int) -> list[dict]:
    """
    Función de búsqueda legacy (compatible con código anterior).
    Crea su propio navegador. Para reutilizar navegador, usar
    crear_navegador_maps() + buscar_en_pagina().
    """
    pw, browser, context, page = crear_navegador_maps()
    try:
        resultado = buscar_en_pagina(page, termino, cantidad)
        return resultado["negocios"]
    finally:
        cerrar_navegador(pw, browser, context)


# --- Para pruebas directas ---
if __name__ == "__main__":
    resultados = buscar_negocios("Restaurantes en Cochabamba", 5)
    for r in resultados:
        console.print(r)
