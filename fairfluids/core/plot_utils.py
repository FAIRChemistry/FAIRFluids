"""
Utility functions for saving matplotlib plots as vector graphics.

This module provides a reusable function for automatically saving plots
from Jupyter notebooks to SVG files with intelligent naming based on plot titles.
"""

import os
import re
import matplotlib.pyplot as plt


_plot_counter = 0


def save_plot_as_svg(filename=None, output_dir='image_output'):
    """
    Speichert den aktuellen Plot als SVG-Datei.
    
    Versucht den Plot-Titel als Dateinamen zu verwenden, verwendet sonst plot_N.svg.
    Jeder Plot erhält einen eindeutigen Dateinamen durch einen Zähler.
    
    Args:
        filename: Optionaler Dateiname. Wenn nicht angegeben, wird der Plot-Titel verwendet.
        output_dir: Verzeichnis zum Speichern der Plots (Standard: 'image_output').
                    Kann relativ zum aktuellen Arbeitsverzeichnis oder absolut sein.
    
    Returns:
        str: Der vollständige Pfad zur gespeicherten Datei.
    
    Example:
        >>> import matplotlib.pyplot as plt
        >>> from fairfluids.core.plot_utils import save_plot_as_svg
        >>> plt.plot([1, 2, 3], [1, 4, 9])
        >>> plt.title("My Plot")
        >>> save_plot_as_svg()  # Speichert als "My_Plot_1.svg"
        >>> plt.show()
    """
    global _plot_counter
    
    try:
        # Erstelle das Ausgabeverzeichnis falls es nicht existiert
        # Verwende absoluten Pfad für Robustheit
        if not os.path.isabs(output_dir):
            # Wenn relativ, erstelle im aktuellen Arbeitsverzeichnis
            abs_output_dir = os.path.abspath(output_dir)
        else:
            abs_output_dir = output_dir
        
        os.makedirs(abs_output_dir, exist_ok=True)
    except Exception as e:
        print(f"Warnung: Konnte Ausgabeverzeichnis nicht erstellen: {e}")
        # Fallback: Versuche im aktuellen Verzeichnis
        abs_output_dir = os.path.abspath('.')
    
    if filename is None:
        # Versuche den Plot-Titel zu extrahieren
        fig = plt.gcf()
        title = None
        
        # Versuche verschiedene Methoden, um den Titel zu finden
        # Zuerst suptitle (für fig.suptitle)
        try:
            if fig._suptitle is not None:
                title = fig._suptitle.get_text()
        except:
            pass
        
        # Dann suche in allen Axes (für ax.set_title oder plt.title)
        if not title:
            try:
                for ax in fig.get_axes():
                    ax_title = ax.get_title()
                    if ax_title:
                        title = ax_title
                        break
            except:
                pass
        
        if title:
            # Bereinige den Titel für Dateinamen
            # Entferne LaTeX-Befehle und Sonderzeichen
            clean_title = re.sub(r'\$.*?\$', '', title)  # Entferne LaTeX-Math
            clean_title = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', clean_title)  # Entferne LaTeX-Befehle
            clean_title = re.sub(r'[^\w\s-]', '', clean_title)  # Entferne Sonderzeichen
            clean_title = re.sub(r'\s+', '_', clean_title)  # Ersetze Leerzeichen mit Unterstrich
            clean_title = re.sub(r'_+', '_', clean_title)  # Entferne mehrfache Unterstriche
            clean_title = clean_title.strip('_')  # Entferne führende/nachfolgende Unterstriche
            clean_title = clean_title[:50]  # Begrenze die Länge
            
            if clean_title:
                # Verwende Titel mit Zähler, um Eindeutigkeit zu gewährleisten
                _plot_counter += 1
                filename = f'{clean_title}_{_plot_counter}'
            else:
                _plot_counter += 1
                filename = f'plot_{_plot_counter}'
        else:
            # Kein Titel gefunden - verwende Fallback
            _plot_counter += 1
            filename = f'plot_{_plot_counter}'
    
    if not filename.endswith('.svg'):
        filename += '.svg'
    
    filepath = os.path.join(abs_output_dir, filename)
    
    try:
        # Prüfe ob ein Plot vorhanden ist
        fig = plt.gcf()
        if fig is None:
            print(f"Warnung: Keine Figure gefunden (plt.gcf() ist None)")
            return None
        
        axes = fig.get_axes()
        if len(axes) == 0:
            print(f"Warnung: Keine Axes im Plot gefunden")
            return None
        
        # Versuche zu speichern
        try:
            plt.savefig(filepath, format='svg', bbox_inches='tight', dpi=300)
        except Exception as save_error:
            print(f"Fehler beim plt.savefig(): {save_error}")
            raise
        
        # Prüfe ob Datei wirklich erstellt wurde
        if not os.path.exists(filepath):
            print(f"Fehler: Datei wurde nicht erstellt: {filepath}")
            print(f"  Aktuelles Arbeitsverzeichnis: {os.getcwd()}")
            print(f"  Absoluter Pfad: {os.path.abspath(filepath)}")
            return None
        
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            print(f"Warnung: Datei ist leer: {filepath}")
            return None
        
        # Erfolgreich gespeichert
        rel_path = os.path.relpath(filepath, os.getcwd()) if os.path.exists(filepath) else filepath
        print(f"✓ Plot gespeichert: {rel_path} ({file_size:,} Bytes)")
        
        return filepath
    except Exception as e:
        print(f"✗ Fehler beim Speichern des Plots: {e}")
        print(f"  Aktuelles Arbeitsverzeichnis: {os.getcwd()}")
        print(f"  Versuchter Pfad: {filepath}")
        import traceback
        traceback.print_exc()
        return None


def reset_plot_counter():
    """
    Setzt den internen Plot-Zähler zurück.
    
    Nützlich, wenn Sie in einem neuen Notebook-Session beginnen möchten
    oder die Nummerierung zurücksetzen möchten.
    """
    global _plot_counter
    _plot_counter = 0
