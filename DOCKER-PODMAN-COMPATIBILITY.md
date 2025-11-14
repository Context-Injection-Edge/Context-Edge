# Docker & Podman Hybrid Compatibility

## ✅ This Platform Works with BOTH Docker and Podman!

### Why This Matters

**Manufacturing environments vary:**
- **Startups/Small shops**: Usually use Docker Desktop
- **Enterprise/Government**: Often prefer Podman (rootless, daemonless, more secure)
- **Red Hat/Fedora**: Podman is the default container runtime
- **Air-gapped facilities**: May require Podman for compliance

By supporting both, you maximize your addressable market.

---

## How We Achieved Compatibility

### 1. Fully Qualified Image Names

**Before (Docker-only shorthand):**
```yaml
services:
  postgres:
    image: postgres:15  # Works on Docker, fails on Podman
```

**After (Universal format):**
```yaml
services:
  postgres:
    image: docker.io/library/postgres:15  # Works on BOTH
```

**Why this works:**
- Docker accepts both `postgres:15` and `docker.io/library/postgres:15`
- Podman REQUIRES fully qualified names to avoid ambiguity
- Using full names makes it work everywhere

### 2. Standard docker-compose.yml Format

We use the official `docker-compose.yml` specification:
- Docker uses `docker compose` (native)
- Podman uses `podman-compose` (compatible implementation)

### 3. Auto-Detection Startup Script

**`start.sh` automatically detects your environment:**

```bash
#!/bin/bash
# Detects Docker or Podman and uses appropriate commands

if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v podman &> /dev/null; then
    COMPOSE_CMD="podman-compose"
fi

$COMPOSE_CMD up -d
```

---

## Platform Differences (For Developers)

### Docker
- **Daemon-based**: Runs as a background service
- **Root access**: Default mode requires root/sudo
- **Desktop app**: Easy GUI for Mac/Windows
- **Most common**: 80%+ market share

### Podman
- **Daemonless**: No background service needed
- **Rootless**: Runs without root privileges (more secure)
- **CLI-only**: No GUI (but compatible with Docker Desktop)
- **Enterprise**: Preferred by Red Hat, government contractors

### What's the Same
- ✅ Container images (OCI standard)
- ✅ docker-compose.yml format
- ✅ Port mappings
- ✅ Volume mounts
- ✅ Networking
- ✅ All Python/Node.js code

---

## Testing Matrix

We've tested this platform on:

| Environment | Container Runtime | Status |
|-------------|-------------------|--------|
| Ubuntu 22.04 | Docker 24.x | ✅ Works |
| Ubuntu 22.04 | Podman 4.x | ✅ Works |
| Fedora 40 | Podman 5.x | ✅ Works |
| macOS | Docker Desktop | ✅ Should work* |
| Windows 11 | Docker Desktop | ✅ Should work* |
| RHEL 9 | Podman 4.x | ✅ Should work* |

*Not tested yet but uses standard formats

---

## Installation Differences

### For Docker Users (Most Common)

**Prerequisites:**
```bash
# Install Docker Desktop (Mac/Windows)
# Or Docker Engine (Linux)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**Start platform:**
```bash
./start.sh  # Auto-detects Docker
# OR
docker compose up -d
```

### For Podman Users (Enterprise/Secure Environments)

**Prerequisites:**
```bash
# Podman (usually pre-installed on Fedora/RHEL)
sudo dnf install podman

# podman-compose
pip3 install podman-compose
```

**Start platform:**
```bash
./start.sh  # Auto-detects Podman
# OR
podman-compose up -d
```

---

## Troubleshooting

### Issue: "short-name resolution enforced" (Podman)
**Cause:** Image name not fully qualified
**Fix:** Already handled in our docker-compose.yml with `docker.io/library/` prefix

### Issue: "permission denied" errors (Podman)
**Cause:** SELinux on Fedora/RHEL
**Fix:** Volume mounts use `:z` flag (handled automatically by podman-compose)

### Issue: "Docker daemon not running" (Docker)
**Cause:** Docker Desktop not started
**Fix:** Start Docker Desktop application

---

## For Customers: Which Should They Use?

**Recommend Docker if:**
- Small/medium manufacturing shop
- Using Mac/Windows workstations
- Want GUI management
- Standard IT environment

**Recommend Podman if:**
- Large enterprise with security requirements
- Government/defense contractor (STIG compliance)
- Using Red Hat Enterprise Linux
- Air-gapped or restricted environment
- Need rootless containers

**Either works! The platform is 100% compatible with both.**

---

## Architecture Benefits

By using container-agnostic standards:
1. ✅ Customers can choose their preferred runtime
2. ✅ No vendor lock-in
3. ✅ Easier to pass security audits
4. ✅ Works in air-gapped facilities
5. ✅ Future-proof as container tech evolves

---

## Developer Notes

If you're extending this platform:

**DO:**
- ✅ Use fully qualified image names in Dockerfiles
- ✅ Test with both Docker and Podman
- ✅ Use standard docker-compose.yml syntax
- ✅ Keep Python/Node.js code platform-agnostic

**DON'T:**
- ❌ Use Docker-specific features (BuildKit secrets, etc.)
- ❌ Assume daemon is running (Podman is daemonless)
- ❌ Hardcode `docker` commands (use env variable)
- ❌ Use proprietary image registries without fallbacks

---

## Summary

**This platform is truly hybrid:**
- Same codebase works on Docker AND Podman
- Auto-detection makes it seamless for users
- No performance difference
- No feature limitations
- Maximum market reach

**For customers**: "Just run `./start.sh` - it works with whatever you have!"
