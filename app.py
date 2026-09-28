from flask import Flask, render_template
import subprocess

app = Flask(__name__)

ADB = r"D:\platform-tools\adb.exe"

def adb(command):
    try:
        result = subprocess.run(
            [ADB] + command.split(),
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except:
        return "N/A"

def get_phone_data():
    return {
        'name':           adb("shell getprop ro.product.marketname"),
        'brand':          adb("shell getprop ro.product.brand"),
        'model':          adb("shell getprop ro.product.model"),
        'android':        adb("shell getprop ro.build.version.release"),
        'security_patch': adb("shell getprop ro.build.version.security_patch"),
        'build':          adb("shell getprop ro.build.display.id"),
        'cpu':            adb("shell getprop ro.product.board"),
        'bootloader':     adb("shell getprop ro.boot.verifiedbootstate"),
        'network':        adb("shell getprop gsm.network.type"),
        'battery':        adb("shell dumpsys battery"),
        'ram':            adb("shell cat /proc/meminfo"),
        'storage':        adb("shell df /data"),
        'serial':         adb("get-serialno"),
    }

def parse_battery(raw):
    level  = 'N/A'
    health = 'N/A'
    temp   = 'N/A'
    status = 'N/A'

    for line in raw.splitlines():
        line = line.strip()

        if line.startswith('level:'):
            level = line.split(':')[1].strip() + '%'

        if line.startswith('health:'):
            h = line.split(':')[1].strip()
            health_map = {
                '2': 'Good', '3': 'Overheat',
                '4': 'Dead', '5': 'Over Voltage', '7': 'Cold'
            }
            health = health_map.get(h, 'Good')

        if line.startswith('temperature:'):
            try:
                t    = int(line.split(':')[1].strip())
                temp = str(t // 10) + '°C'
            except:
                temp = 'N/A'

        if line.startswith('status:'):
            s = line.split(':')[1].strip()
            status_map = {
                '1': 'Unknown', '2': 'Charging',
                '3': 'Discharging', '4': 'Not Charging', '5': 'Full'
            }
            status = status_map.get(s, 'Unknown')

    return {
        'level':  level,
        'health': health,
        'temp':   temp,
        'status': status
    }

def parse_ram(raw):
    total   = 'N/A'
    free_gb = 0
    total_gb = 0

    for line in raw.splitlines():
        if line.startswith('MemTotal:'):
            try:
                kb       = int(line.split()[1])
                total_gb = round(kb / 1024 / 1024, 1)
                total    = str(total_gb) + ' GB'
            except:
                pass
        if line.startswith('MemAvailable:'):
            try:
                kb      = int(line.split()[1])
                free_gb = round(kb / 1024 / 1024, 1)
            except:
                pass

    used_gb = round(total_gb - free_gb, 1)
    return {
        'total': total,
        'free':  str(free_gb) + ' GB',
        'used':  str(used_gb) + ' GB'
    }

def parse_storage(raw):
    try:
        for line in raw.strip().splitlines():
            if '/data' in line:
                parts    = line.split()
                total_kb = int(parts[1])
                used_kb  = int(parts[2])
                total_gb = round(total_kb / 1024 / 1024, 1)
                used_gb  = round(used_kb  / 1024 / 1024, 1)
                pct      = int((used_gb / total_gb) * 100) if total_gb > 0 else 0
                return {
                    'total': str(total_gb) + ' GB',
                    'used':  str(used_gb)  + ' GB',
                    'pct':   str(pct)
                }
    except:
        pass
    return {'total': 'N/A', 'used': 'N/A', 'pct': '0'}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    raw     = get_phone_data()
    battery = parse_battery(raw['battery'])
    ram     = parse_ram(raw['ram'])
    storage = parse_storage(raw['storage'])

    # use model if marketname is empty
    name = raw['name'] if raw['name'] and raw['name'] != 'N/A' else raw['model']

    data = {
        'name':           name,
        'brand':          raw['brand'],
        'model':          raw['model'],
        'android':        raw['android'],
        'security_patch': raw['security_patch'],
        'build':          raw['build'],
        'cpu':            raw['cpu'],
        'bootloader':     raw['bootloader'].upper() if raw['bootloader'] not in ['N/A', ''] else 'N/A',
        'network':        raw['network'],
        'serial':         raw['serial'],

        'battery_level':  battery['level'],
        'battery_health': battery['health'],
        'battery_temp':   battery['temp'],
        'battery_status': battery['status'],

        'ram_total': ram['total'],
        'ram_free':  ram['free'],
        'ram_used':  ram['used'],

        'storage_total': storage['total'],
        'storage_used':  storage['used'],
        'storage_pct':   storage['pct'],

        'health_score': '85',
    }
    return render_template('dashboard.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)