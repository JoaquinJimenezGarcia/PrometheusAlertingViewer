## Prometheus Alerting
Expansion to see in the desktop if you have any alert firing on your Prometheus instance.

> Note: This has only been tested on Ubuntu 24.04

### How it works.
It just make a simple request to your Prometheus API and return the alerts. Modify the `PROMETHEUS_URL` and `SCRAPE_INTERVAL` values in order to meet with your requirements.

I have it running in the background as a daemon:
`vim ~/.config/systemd/user/prometheus-tray.service`
```
[Unit]
Description=Prometheus Alerts Tray Indicator
After=graphical-session.target network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /PATH/PrometheusAlerting/prometheus_tray.py
Restart=always
RestartSec=5

# Required for tray icons / GTK apps
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/%U

[Install]
WantedBy=default.target
```

> Make sure to change `PATH` to the current value where you download the project.


```
systemctl --user daemon-reload
systemctl --user enable prometheus-tray.service
systemctl --user start prometheus-tray.service
```