# Custody Calendar

Persistent self-hosted custody calendar for Unraid / Byte-Me.

## Features
- Mum/Dad AM/PM calendar
- Existing alternating weekend rules preserved
- Negotiable handovers
- Persistent SQLite storage
- CSV import/export using `custody-schedule-YYYY-MM.csv`
- Database backup
- Mobile-friendly UI
- Docker/Compose deployment

## Install on Byte-Me

```bash
cd /boot/config/plugins/compose.manager/projects
git clone https://github.com/adamrfreeman644/Custody-Calendar.git custody-calendar
cd custody-calendar
docker compose up -d --build
```

Open:

```
http://192.168.1.187:8098
```

Persistent data is stored at:

```
/mnt/user/appdata/custody-calendar/custody.db
```

## Update

```bash
cd /boot/config/plugins/compose.manager/projects/custody-calendar
git pull
docker compose up -d --build
docker image prune -f
```

## Backup

Use **Backup database** in the app, or copy:

```
/mnt/user/appdata/custody-calendar/custody.db
```

## Port

Default host port is **8098**. Change the left side of this line in `docker-compose.yml` if needed:

```yaml
ports:
  - "8098:8080"
```
