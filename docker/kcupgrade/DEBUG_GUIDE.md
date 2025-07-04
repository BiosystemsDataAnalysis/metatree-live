# Bash Script Testing and Debugging Guide

## 🐛 Debug Your import_users.sh Script

### **Available Debug Modes**

#### 1. **Normal Mode (Production)**
```bash
./import_users.sh
```
- Clean output with INFO/WARN/ERROR messages
- Actual imports performed
- Best for production use

#### 2. **Debug Mode (Verbose)**
```bash
DEBUG=true ./import_users.sh
```
- Detailed trace of all commands
- Shows variable values and API calls
- Shows user data being processed
- Useful for troubleshooting

#### 3. **Dry Run Mode (Safe Testing)**
```bash
DRY_RUN=true ./import_users.sh
```
- Shows what would be imported without making changes
- No actual API calls to create users
- Safe for testing configuration

#### 4. **Skip Existing Users**
```bash
SKIP_EXISTING=true ./import_users.sh
```
- Checks if users exist before importing
- Skips existing users silently
- Useful for incremental imports

#### 5. **Combined Modes**
```bash
DEBUG=true DRY_RUN=true ./import_users.sh
DEBUG=true SKIP_EXISTING=true ./import_users.sh
```

### **VS Code Debugging Options**

#### **Method 1: Use VS Code Tasks**
1. Press `Ctrl+Shift+P` → "Tasks: Run Task"
2. Select "Debug import_users.sh"
3. View output in integrated terminal

#### **Method 2: Use Debug Panel**
1. Press `Ctrl+Shift+D` (Run and Debug)
2. Select "Debug import_users.sh (bash -x)"
3. Click play button to run with bash tracing

#### **Method 3: Use ShellCheck Integration**
- Red squiggly lines show potential issues
- Hover over them for suggestions
- Automatic linting as you type

### **Common Debug Scenarios**

#### **Test Configuration**
```bash
# Test without making changes
DRY_RUN=true DEBUG=true ./import_users.sh
```

#### **Check for Existing Users**
```bash
# Skip users that already exist
SKIP_EXISTING=true ./import_users.sh
```

#### **Debug Authentication Issues**
```bash
# Show detailed auth process
DEBUG=true ./import_users.sh | head -20
```

#### **Debug JSON Processing**
```bash
# Test JSON parsing
DEBUG=true ./import_users.sh 2>&1 | grep -E "(DEBUG|jq)"
```

### **Error Handling Features**

The script includes:
- **Exit on error**: `set -e`
- **Exit on undefined variables**: `set -u`
- **Exit on pipeline failures**: `set -o pipefail`
- **Comprehensive error messages**
- **Import summaries**
- **Temporary file cleanup**

### **Testing Checklist**

- [ ] Run in dry-run mode first
- [ ] Check Keycloak connectivity
- [ ] Verify JSON file structure
- [ ] Test with debug mode
- [ ] Check import summary
- [ ] Verify users in Keycloak admin console

### **Troubleshooting Tips**

1. **Authentication fails**: Check ADMIN_USERNAME/ADMIN_PASSWORD
2. **JSON parsing errors**: Verify file structure with `jq . file.json`
3. **Users already exist**: Use `SKIP_EXISTING=true`
4. **Network issues**: Check KEYCLOAK_URL accessibility
5. **Permission errors**: Ensure script is executable (`chmod +x`)

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable verbose debugging |
| `DRY_RUN` | `false` | Show actions without executing |
| `SKIP_EXISTING` | `false` | Skip existing users |
| `KEYCLOAK_URL` | `http://localhost:8080` | Keycloak server URL |
| `ADMIN_USERNAME` | `admin` | Admin username |
| `ADMIN_PASSWORD` | `admin` | Admin password |
| `REALM` | `metatree` | Target realm |
| `IMPORT_FILE` | `./keycloak_users_import_formatted.json` | JSON file to import |
