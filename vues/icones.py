"""Icônes SVG inline (trait fin, currentColor). Aucun emoji dans l'application."""
from __future__ import annotations

_CHEMINS = {
    "tableau": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    "thermometre": '<path d="M14 14.8V5a2 2 0 0 0-4 0v9.8a4 4 0 1 0 4 0z"/><path d="M12 9v7"/>',
    "goutte": '<path d="M12 3s6 6.2 6 10.5A6 6 0 0 1 6 13.5C6 9.2 12 3 12 3z"/>',
    "ventilateur": '<circle cx="12" cy="12" r="1.8"/><path d="M12 10.2C12 6 10.5 3.5 8 3.5c-2 0-2.5 2.2-1 3.6 1.2 1.2 3.2 2 5 3.1z"/><path d="M13.8 12c4.2 0 6.7-1.5 6.7-4 0-2-2.2-2.5-3.6-1-1.2 1.2-2 3.2-3.1 5z"/><path d="M12 13.8c0 4.2 1.5 6.7 4 6.7 2 0 2.5-2.2 1-3.6-1.2-1.2-3.2-2-5-3.1z"/><path d="M10.2 12c-4.2 0-6.7 1.5-6.7 4 0 2 2.2 2.5 3.6 1 1.2-1.2 2-3.2 3.1-5z"/>',
    "pompe": '<circle cx="11" cy="13" r="6"/><path d="M11 13l3.5-3.5"/><path d="M17 13h4"/><path d="M11 7V4h5"/><path d="M5 19h12"/>',
    "compresseur": '<rect x="3" y="7" width="14" height="10" rx="2"/><path d="M17 10h4v4h-4"/><path d="M7 11l3 2-3 2"/><path d="M7 4v3M13 4v3"/>',
    "eclair": '<path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/>',
    "monnaie": '<circle cx="12" cy="12" r="9"/><path d="M14.8 9.2c-.6-1-1.700-1.500-2.800-1.500-1.600 0-2.800.9-2.800 2.200 0 3 5.800 1.500 5.800 4.500 0 1.300-1.200 2.200-2.900 2.200-1.300 0-2.500-.6-3-1.700"/><path d="M12 6v1.700M12 16.300V18"/>',
    "alerte": '<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5"/><path d="M12 18v.01"/>',
    "valide": '<circle cx="12" cy="12" r="9"/><path d="M8 12.500l3 3 5-6"/>',
    "capteur": '<circle cx="12" cy="12" r="3"/><path d="M6.300 6.300a8 8 0 0 0 0 11.400M17.700 6.300a8 8 0 0 1 0 11.400M3.500 3.500a12 12 0 0 0 0 17M20.500 3.500a12 12 0 0 1 0 17"/>',
    "upload": '<path d="M12 16V4"/><path d="M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
    "download": '<path d="M12 4v12"/><path d="M7 11l5 5 5-5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
    "reglages": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.900 4.900l2.100 2.100M17 17l2.100 2.100M4.900 19.100L7 17M17 7l2.100-2.100"/>',
    "cle": '<path d="M14.700 6.300a4 4 0 0 0-5.400 5.100L3 17.700V21h3.300l6.300-6.300a4 4 0 0 0 5.100-5.400L15 12l-3-3 2.700-2.700z"/>',
    "horloge": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "graphique": '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>',
    "tendance_haut": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "tendance_bas": '<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>',
    "cycle": '<path d="M4 8h12a4 4 0 0 1 0 8H8"/><path d="M7 5L4 8l3 3"/><path d="M17 13l3 3-3 3"/>',
    "base_donnees": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.700 3.600 3 8 3s8-1.300 8-3V5"/><path d="M4 12c0 1.700 3.600 3 8 3s8-1.300 8-3"/>',
    "mollier": '<path d="M3 20V4"/><path d="M3 20h18"/><path d="M5 18C7 8 10 5 12 5s5 3 7 13"/><path d="M8 14h9"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><path d="M12 7.500v.01"/>',
    "usine": '<path d="M3 21V10l6 4V10l6 4V6l6-3v18H3z"/><path d="M7 17h2M12 17h2M17 17h2"/>',
    "livre": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5z"/><path d="M4 19a2 2 0 0 1 2-2h13"/>',
    "calque": '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
    "sante": '<path d="M3 12h4l2-5 4 10 2-5h6"/>',
    "play": '<path d="M7 4l13 8-13 8V4z"/>',
    "pause": '<path d="M8 4v16M16 4v16"/>',
}


def icone(nom: str, taille: int = 20, couleur: str | None = None, epaisseur: float = 1.7) -> str:
    chemin = _CHEMINS.get(nom, _CHEMINS["info"])
    style = f' style="color:{couleur}"' if couleur else ""
    return (f'<svg class="ic" width="{taille}" height="{taille}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="{epaisseur}" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true"{style}>{chemin}</svg>')


def favicon_svg() -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#33C2D6" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + _CHEMINS["thermometre"] + "</svg>")
