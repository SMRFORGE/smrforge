# Dashboard Troubleshooting Guide

**Last Updated:** January 2026

Common issues and solutions for the SMRForge web dashboard.

---

## Issue: Dashboard Won't Start

### Error: "Dash is not installed" or "ModuleNotFoundError: No module named 'dash'"

**Solution:**
```bash
# Install dashboard dependencies
pip install dash dash-bootstrap-components

# Or install all visualization dependencies
pip install smrforge[viz]
```

**Verify Installation:**
```bash
python -c "import dash; import dash_bootstrap_components; print('Dashboard dependencies installed!')"
```

---

## Issue: Dashboard Starts But Shows Blank Page

### Possible Causes:

1. **JavaScript Errors in Browser Console**
   - Open browser developer tools (F12)
   - Check Console tab for errors
   - Check Network tab for failed resource loads

2. **Theme Loading Issues**
   - Dashboard uses Bootswatch CDN for themes
   - Check internet connection
   - Try refreshing the page

3. **Port Already in Use**
   ```bash
   # Use different port
   smrforge serve --port 8051
   ```

---

## Issue: "Port Already in Use"

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Option 1: Use different port
smrforge serve --port 8051

# Option 2: Find and kill process using port 8050
# Windows:
netstat -ano | findstr :8050
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8050 | xargs kill
```

---

## Issue: Dashboard Not Accessible from Network

**Problem:** Dashboard only accessible from localhost

**Solution:**
```bash
# Run with host 0.0.0.0 to allow network access
smrforge serve --host 0.0.0.0 --port 8050
```

**Security Note:** Only use `0.0.0.0` on trusted networks or with proper firewall rules.

---

## Issue: Import Errors

### Error: "Failed to import dashboard module"

**Check:**
1. SMRForge is properly installed:
   ```bash
   python -c "import smrforge; print(smrforge.__version__)"
   ```

2. GUI module is available:
   ```bash
   python -c "from smrforge.gui import run_server; print('GUI available')"
   ```

3. All dependencies are installed:
   ```bash
   pip list | grep -E "dash|plotly"
   ```

---

## Issue: Theme Not Switching

**Problem:** Theme selector doesn't change appearance

**Solution:**
1. Check browser console for JavaScript errors
2. Clear browser cache and refresh
3. Try different browser
4. Check internet connection (themes load from CDN)

---

## Issue: Components Not Loading

**Problem:** Reactor builder, analysis panel, etc. not showing

**Possible Causes:**
1. **Missing SMRForge Core Dependencies**
   ```bash
   pip install -e .
   ```

2. **Import Errors in Components**
   - Check Python console for import errors
   - Verify all SMRForge modules are installed

3. **Callback Registration Issues**
   - Run with debug mode: `smrforge serve --debug`
   - Check terminal for callback errors

---

## Issue: Dashboard Crashes on Analysis

**Problem:** Dashboard crashes when running analysis

**Possible Causes:**
1. **Missing ENDF Data**
   - Set up ENDF files first
   - Use data downloader: `from smrforge.data_downloader import download_endf_data`

2. **Missing Core Dependencies**
   - Ensure all SMRForge dependencies are installed
   - Check: `pip install -e .`

3. **Validation Errors**
   - Check reactor specification is valid
   - Review error messages in dashboard

---

## Debugging Steps

### 1. Check Dependencies
```bash
# Check if Dash is installed
python -c "import dash; print('Dash:', dash.__version__)"

# Check if dash-bootstrap-components is installed
python -c "import dash_bootstrap_components; print('DBC available')"

# Check SMRForge GUI module
python -c "from smrforge.gui import create_app; app = create_app(); print('App created:', app is not None)"
```

### 2. Run with Debug Mode
```bash
smrforge serve --debug
```

This will show:
- Detailed error messages
- Callback registration issues
- Import errors

### 3. Check Browser Console
1. Open dashboard in browser
2. Press F12 to open developer tools
3. Check Console tab for JavaScript errors
4. Check Network tab for failed requests

### 4. Test Minimal Dashboard
```python
from smrforge.gui import create_app

app = create_app()
if app:
    print("Dashboard app created successfully")
    # Dash 3.x uses app.run(), Dash 2.x uses app.run_server()
    if hasattr(app, 'run'):
        app.run(debug=True, port=8050)
    else:
        app.run_server(debug=True, port=8050)
else:
    print("Failed to create dashboard app")
```

---

## Common Error Messages

### "Dash is not available"
**Solution:** `pip install dash dash-bootstrap-components`

### "Failed to create Dash application"
**Solution:** Check all dependencies are installed and SMRForge is properly set up

### "Address already in use"
**Solution:** Use different port or kill process using port 8050

### "Connection refused"
**Solution:** 
- Check dashboard is running
- Verify port number
- Check firewall settings

---

## Getting Help

If issues persist:

1. **Check Logs:**
   ```bash
   smrforge serve --debug 2>&1 | tee dashboard.log
   ```

2. **Verify Installation:**
   ```bash
   pip list | grep -E "smrforge|dash|plotly"
   ```

3. **Test Minimal Example:**
   ```python
   import dash
   from dash import html
   app = dash.Dash(__name__)
   app.layout = html.Div("Test")
   # Dash 3.x uses app.run(), Dash 2.x uses app.run_server()
   if hasattr(app, 'run'):
       app.run(debug=True)
   else:
       app.run_server(debug=True)
   ```

4. **Check Documentation:**
   - [Dashboard Guide](dashboard-guide.md)
   - [Installation Guide](../guides/installation.md)

---

## Quick Fix Checklist

- [ ] Dash installed: `pip install dash dash-bootstrap-components`
- [ ] SMRForge installed: `pip install -e .`
- [ ] Port 8050 available (or use different port)
- [ ] Browser can access http://127.0.0.1:8050
- [ ] No firewall blocking port
- [ ] Running latest version of SMRForge
- [ ] Python 3.8+ installed

---

**See Also:**
- [Dashboard Guide](dashboard-guide.md) - Complete dashboard documentation
- [Installation Guide](installation.md) - Installation instructions
- [Usage Guide](usage.md) - General SMRForge usage
