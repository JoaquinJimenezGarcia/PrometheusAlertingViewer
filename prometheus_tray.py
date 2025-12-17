#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")

from gi.repository import Gtk, AppIndicator3, GLib
import threading
import time
import requests
import os

PROMETHEUS_URL = "http://server1:9090"
SCRAPE_INTERVAL = 20
# We use a standard system icon as a fallback/base
DEFAULT_ICON = "dialog-information" 

active_alerts = []
# Threading lock to prevent reading while writing
data_lock = threading.Lock()

# ---------------- Fetch alerts -----------------
def fetch_alerts():
    global active_alerts
    while True:
        try:
            r = requests.get(f"{PROMETHEUS_URL}/api/v1/alerts", timeout=5)
            data = r.json()
            firing = [a for a in data["data"]["alerts"] if a["state"] == "firing"]

            with data_lock:
                active_alerts = firing
        except Exception as e:
            with data_lock:
                active_alerts = [{
                    "labels": {"alertname": "Prometheus unreachable"},
                    "annotations": {"description": str(e)}
                }]
        time.sleep(SCRAPE_INTERVAL)

# ---------------- Tray app -----------------
class PrometheusTray:
    def __init__(self):
        # Initialize indicator with a label
        self.indicator = AppIndicator3.Indicator.new(
            "prometheus-alerts",
            DEFAULT_ICON,
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        
        # This is the magic part: set an initial label
        self.indicator.set_label("PromAlerts(0)", "")

        self.menu = Gtk.Menu()
        self.indicator.set_menu(self.menu)

        # Refresh more frequently than the scrape interval to keep UI snappy
        GLib.timeout_add_seconds(5, self.refresh_ui)
        self.refresh_ui()

    def refresh_ui(self):
        with data_lock:
            alerts = list(active_alerts)
        
        count = len(alerts)
        
        # 1. Update the Text Label in the top bar
        label_text = f"PromAlerts({count})"
        self.indicator.set_label(label_text, "")

        # 2. Update Icon based on severity
        if count > 0:
            self.indicator.set_icon_full("dialog-warning", "Alerts Firing")
        else:
            self.indicator.set_icon_full("emblem-ok-symbolic", "No Alerts")

        # 3. Rebuild Menu
        for item in self.menu.get_children():
            self.menu.remove(item)

        if count == 0:
            item = Gtk.MenuItem(label="✅ No active alerts")
            item.set_sensitive(False)
            self.menu.append(item)
        else:
            for alert in alerts:
                name = alert["labels"].get("alertname", "Unknown")
                desc = alert["annotations"].get("description", "No description")
                # Clean up description for the menu
                desc_short = desc.split("\n")[0][:60]
                item = Gtk.MenuItem(label=f"🚨 {name}: {desc_short}")
                self.menu.append(item)

        self.menu.append(Gtk.SeparatorMenuItem())
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", Gtk.main_quit)
        self.menu.append(quit_item)

        self.menu.show_all()
        return True

# ---------------- Main -----------------
if __name__ == "__main__":
    # Start the fetcher thread
    t = threading.Thread(target=fetch_alerts, daemon=True)
    t.start()
    
    # Run the GTK loop
    tray = PrometheusTray()
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass